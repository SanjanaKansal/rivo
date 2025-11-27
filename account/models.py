from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')

    def __str__(self):
        return self.name


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email or self.username

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        if self.role and self.role.permissions.filter(codename=perm.split('.')[-1]).exists():
            return True
        return super().has_perm(perm, obj)

    @property
    def can_view_all(self):
        return self.has_perm('client.view_all_clients')

    @property
    def can_assign(self):
        return self.has_perm('client.assign_client')

    @property
    def can_change_stage(self):
        return self.has_perm('client.change_client_stage')
