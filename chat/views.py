from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatHistory, Client
from .serializers import ChatHistorySerializer, SendMessageSerializer
import re


class ChatViewSet(viewsets.ViewSet):
    """
    Simple chat service - just send messages and get history

    Endpoints:
    - POST /chat/stream/ - Send a message
    - GET /chat/history/?session_id=<uuid> - Get chat history
    """

    @action(detail=False, methods=['post'])
    def stream(self, request):
        """
        Send a message and add it to chat history

        POST /chat/stream/
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "message": "Hello!",
            "sender_type": "client",
            "data_type": "message"  // optional, defaults to 'message'
        }
        """
        serializer = SendMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']
        sender_type = serializer.validated_data['sender_type']
        data_type = serializer.validated_data.get('data_type', 'message')

        # Get existing client for this session (if any)
        client = self._get_client_for_session(session_id)

        # If data_type is name/email/phone, create/update client
        if data_type in ['name', 'email', 'phone']:
            if not client:
                client = Client.objects.create()
            self._update_client_info(client, data_type, message)

        # Create the chat message
        chat_message = ChatHistory.objects.create(
            session_id=session_id,
            client=client,
            message=message,
            sender_type=sender_type,
            data_type=data_type
        )

        # Return the created message
        response_serializer = ChatHistorySerializer(chat_message)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get chat history for a specific session

        GET /chat/history/?session_id=550e8400-e29b-41d4-a716-446655440000
        """
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response(
                {'error': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all messages for this session
        messages = ChatHistory.objects.filter(session_id=session_id)
        serializer = ChatHistorySerializer(messages, many=True)

        return Response({
            'session_id': session_id,
            'messages': serializer.data
        })

    def _get_client_for_session(self, session_id):
        """Get existing client for this session (if any)"""
        chat_history = ChatHistory.objects.filter(
            session_id=session_id,
            client__isnull=False
        ).first()
        return chat_history.client if chat_history else None

    def _update_client_info(self, client, data_type, message):
        """Update client information based on data type"""
        if data_type == 'name':
            client.name = message.strip().title()
        elif data_type == 'email':
            client.email = message.strip().lower()
        elif data_type == 'phone':
            phone_clean = re.sub(r'\D', '', message)
            client.phone_number = phone_clean
        client.save()