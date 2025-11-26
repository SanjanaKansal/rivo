from rest_framework import serializers
from .models import ChatHistory
import uuid


class ChatHistorySerializer(serializers.ModelSerializer):
    """Serializer for chat history messages"""

    class Meta:
        model = ChatHistory
        fields = ['id', 'session_id', 'message', 'sender_type', 'sent_at']
        read_only_fields = ['id', 'sent_at']

    def validate_sender_type(self, value):
        """Validate sender_type is one of the allowed choices"""
        allowed_types = ['bot', 'client']
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"sender_type must be one of: {', '.join(allowed_types)}"
            )
        return value


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message to a chat session"""
    session_id = serializers.UUIDField()
    message = serializers.CharField()
    sender_type = serializers.ChoiceField(
        choices=['bot', 'client'],
        default='client'
    )

    def validate_message(self, value):
        """Ensure message is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class ChatSessionHistorySerializer(serializers.Serializer):
    """Serializer for retrieving chat history for a session"""
    session_id = serializers.UUIDField()
    messages = ChatHistorySerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(read_only=True)