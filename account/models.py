from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Base model with created_at and updated_at fields
    """
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    """
    Role model for defining different user roles with specific permissions
    """
    name = models.CharField(_('name'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
        related_name='role_permissions'
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('role')
        verbose_name_plural = _('roles')

    def __str__(self):
        return self.name


class User(AbstractUser, BaseModel):
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    is_active = models.BooleanField(_('active'), default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email or self.username or str(self.id)

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        if self.role and self.role.permissions.filter(codename=perm.split('.')[-1]).exists():
            return True
        return super().has_perm(perm, obj)

    def get_permissions(self):
        """Get dashboard permissions dict"""
        return {
            'can_view_all': self.has_perm('client.view_all_clients'),
            'can_assign': self.has_perm('client.assign_client'),
            'can_change_stage': self.has_perm('client.change_client_stage'),
        }
