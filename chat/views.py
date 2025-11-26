from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatHistory
from .serializers import ChatHistorySerializer, SendMessageSerializer


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

        POST /chat/stream//
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "message": "Hello!",
            "sender_type": "client"
        }
        """
        serializer = SendMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the chat message
        chat_message = ChatHistory.objects.create(
            session_id=serializer.validated_data['session_id'],
            message=serializer.validated_data['message'],
            sender_type=serializer.validated_data['sender_type']
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