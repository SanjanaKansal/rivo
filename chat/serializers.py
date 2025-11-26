from rest_framework import serializers
from .models import ChatHistory


class ChatHistorySerializer(serializers.ModelSerializer):
    """Serializer for chat history messages"""

    class Meta:
        model = ChatHistory
        fields = ['id', 'session_id', 'message', 'sender_type', 'data_type', 'sent_at']
        read_only_fields = ['id', 'sent_at']


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message to a chat session"""
    session_id = serializers.UUIDField()
    message = serializers.CharField()
    sender_type = serializers.ChoiceField(
        choices=['bot', 'client'],
        default='client'
    )
    data_type = serializers.ChoiceField(
        choices=['message', 'name', 'email', 'phone'],
        default='message',
        required=False
    )

    def validate_message(self, value):
        """Ensure message is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()