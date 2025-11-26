from django.db import models
from account.models import BaseModel, User
from django.utils.translation import gettext_lazy as _


class Client(BaseModel):
    """
    Client/Lead model with stage tracking
    """
    STAGE_CHOICES = [
        ('lead', 'Lead'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('docs_pending', 'Docs Pending'),
        ('docs_received', 'Docs Received'),
        ('application_started', 'Application Started'),
        ('application_submitted', 'Application Submitted'),
        ('application_in_process', 'Application In Process'),
        ('application_approved', 'Application Approved'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('lost', 'Lost'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, db_index=True)
    current_stage = models.CharField(
        max_length=50,
        choices=STAGE_CHOICES,
        default='lead',
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('client')
        verbose_name_plural = _('clients')
        indexes = [
            models.Index(fields=['email', 'phone']),
            models.Index(fields=['current_stage', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.current_stage}"

    @property
    def is_complete(self):
        """Helper to check if info is complete"""
        return all([self.name, self.email, self.phone])


class ClientStageHistory(BaseModel):
    """
    Tracks all stage transitions for a client
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='stage_history'
    )
    from_stage = models.CharField(max_length=50, blank=True)
    to_stage = models.CharField(max_length=50)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stage_changes',
        help_text="User who made this stage change"
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('client stage history')
        verbose_name_plural = _('client stage histories')
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]

    def __str__(self):
        if self.from_stage:
            return f"{self.client.name}: {self.from_stage} → {self.to_stage}"
        return f"{self.client.name}: → {self.to_stage}"


class ClientAssignment(BaseModel):
    """
    Manages client assignments to CS users
    Uses Foreign Keys for all user references instead of UUIDs
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text="Client being assigned"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_clients',
        help_text="Customer Support user assigned to this client"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made',
        help_text="User who made this assignment"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('client assignment')
        verbose_name_plural = _('client assignments')
        indexes = [
            models.Index(fields=['assigned_to', 'is_active']),
            models.Index(fields=['client', 'is_active']),
        ]
        # Ensure only one active assignment per client
        constraints = [
            models.UniqueConstraint(
                fields=['client'],
                condition=models.Q(is_active=True),
                name='unique_active_assignment'
            )
        ]

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        assigned_to_name = self.assigned_to.get_full_name() if self.assigned_to else "Unknown"
        return f"{self.client.name} → {assigned_to_name} ({status})"