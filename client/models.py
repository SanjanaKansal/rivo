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

    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(db_index=True, blank=True)
    phone = models.CharField(max_length=20, db_index=True, blank=True)
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI-summarized context (intent, preferences, etc.)"
    )
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
        return all([self.name, self.email, self.phone])

    def set_stage(self, new_stage, changed_by=None, remarks=''):
        """Change stage and create history record"""
        if new_stage != self.current_stage:
            ClientStageHistory.objects.create(
                client=self, from_stage=self.current_stage, to_stage=new_stage, 
                changed_by=changed_by, remarks=remarks
            )
            self.current_stage = new_stage
            self.save()

    def assign(self, assigned_to=None, assigned_by=None, remarks=''):
        """Assign client to a user, deactivating previous assignment"""
        ClientAssignment.objects.filter(client=self, is_active=True).update(is_active=False)
        ClientAssignment.objects.create(client=self, assigned_to=assigned_to, assigned_by=assigned_by, is_active=True, remarks=remarks)

    def initialize(self, context=None, remarks='Client information collected via chat.'):
        """Initialize new client workflow - set stage and create pending assignment"""
        if self.stage_history.exists():
            return
        if context:
            self.context = context
            self.save()
        self.set_stage('lead', remarks=remarks)
        self.assign(remarks='Awaiting assignment')


class ClientStageHistory(BaseModel):
    """
    Tracks all stage transitions for a client
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='stage_history'
    )
    from_stage = models.CharField(max_length=50, blank=True, null=True)
    to_stage = models.CharField(max_length=50)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        null=True,
        blank=True,
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