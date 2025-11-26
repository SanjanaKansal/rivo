from django.contrib import admin
from .models import ChatHistory


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ChatHistory model"""

    list_display = ['id', 'session_id', 'sender_type', 'message_preview', 'sent_at']
    list_filter = ['sender_type', 'sent_at']
    search_fields = ['session_id', 'message']
    date_hierarchy = 'sent_at'
    ordering = ['-sent_at']
    readonly_fields = ['sent_at']

    def message_preview(self, obj):
        """Show a preview of the message"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message