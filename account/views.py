from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, email=email, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token, _ = Token.objects.get_or_create(user=user)  # type: ignore
    return Response({
        'token': token.key,
        'user': {'id': user.id, 'email': user.email, 'name': user.get_full_name() or user.email}
    })
