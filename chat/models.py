from django.db import models
from django.utils.translation import gettext_lazy as _

from client.models import Client


class ChatHistory(models.Model):
    """
    Store all chat messages
    Used for chatbot conversations (no authentication required)
    """
    SENDER_TYPE_CHOICES = [
        ('bot', 'Bot'),
        ('client', 'Client'),
    ]

    DATA_TYPE_CHOICES = [
        ('message', 'Regular Message'),
        ('name', 'Name'),
        ('email', 'Email'),
        ('phone', 'Phone Number'),
    ]

    session_id = models.UUIDField(db_index=True)  # Groups messages by session
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='message',
        help_text='Type of data being sent (for client info collection)'
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        verbose_name = _('chat history')
        verbose_name_plural = _('chat histories')
        indexes = [
            models.Index(fields=['session_id', 'sent_at']),
        ]

    def __str__(self):
        return f"{self.sender_type} - {self.data_type} - {self.sent_at}"