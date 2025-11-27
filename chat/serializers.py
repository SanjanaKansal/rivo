import re
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

    def validate(self, data):
        """Cross-field validation for name and email"""
        message = data.get('message', '').strip()
        data_type = data.get('data_type', 'message')

        if data_type == 'name':
            if len(message) < 2:
                raise serializers.ValidationError({
                    'message': 'Name must be at least 2 characters'
                })
            if len(message) > 100:
                raise serializers.ValidationError({
                    'message': 'Name must be less than 100 characters'
                })
            if not re.match(r'^[a-zA-Z\s\.\-\']+$', message):
                raise serializers.ValidationError({
                    'message': 'Name can only contain letters, spaces, dots, hyphens, and apostrophes'
                })

        elif data_type == 'email':
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, message):
                raise serializers.ValidationError({
                    'message': 'Please provide a valid email address'
                })

        elif data_type == 'phone':
            phone_digits = re.sub(r'\D', '', message)
            if len(phone_digits) < 10:
                raise serializers.ValidationError({
                    'message': 'Phone number must have at least 10 digits'
                })

        return data