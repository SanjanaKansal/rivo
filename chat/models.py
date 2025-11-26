from django.db import models
from django.utils.translation import gettext_lazy as _


class ChatHistory(models.Model):
    """
    Store all chat messages
    Used for chatbot conversations (no authentication required)
    """
    SENDER_TYPE_CHOICES = [
        ('bot', 'Bot'),
        ('client', 'Client'),
    ]

    session_id = models.UUIDField(db_index=True)  # Groups messages by session
    message = models.TextField()
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        verbose_name = _('chat history')
        verbose_name_plural = _('chat histories')
        indexes = [
            models.Index(fields=['session_id', 'sent_at']),
        ]

    def __str__(self):
        return f"[{self.session_id}] {self.sender_type}: {self.message[:50]}..."