from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from client.services import summarize_chat_history
from .models import ChatHistory, Client
from .serializers import ChatHistorySerializer, SendMessageSerializer
import re


class ChatViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def stream(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']
        sender_type = serializer.validated_data['sender_type']
        data_type = serializer.validated_data.get('data_type', 'message')

        client = self._get_client(session_id)

        if data_type in ['name', 'email', 'phone']:
            if not client:
                client = Client.objects.create()
                ChatHistory.objects.filter(session_id=session_id, client__isnull=True).update(client=client)

            self._update_client(client, data_type, message)

            if client.is_complete:
                messages = ChatHistory.objects.filter(session_id=session_id, data_type='message').values('sender_type', 'message')
                client.initialize(context=summarize_chat_history(list(messages)))

        chat = ChatHistory.objects.create(
            session_id=session_id, client=client, message=message, sender_type=sender_type, data_type=data_type
        )
        return Response(ChatHistorySerializer(chat).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def history(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=status.HTTP_400_BAD_REQUEST)
        messages = ChatHistory.objects.filter(session_id=session_id)
        return Response({'session_id': session_id, 'messages': ChatHistorySerializer(messages, many=True).data})

    def _get_client(self, session_id):
        chat = ChatHistory.objects.filter(session_id=session_id, client__isnull=False).first()
        return chat.client if chat else None

    def _update_client(self, client, data_type, message):
        if data_type == 'name':
            client.name = message.strip().title()
        elif data_type == 'email':
            client.email = message.strip().lower()
        elif data_type == 'phone':
            client.phone = re.sub(r'\D', '', message)
        client.save()
