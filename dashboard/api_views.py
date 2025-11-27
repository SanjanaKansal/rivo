from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from client.models import Client, ClientAssignment, ClientStageHistory
from account.models import User


def get_user_permissions(user):
    """Get user's dashboard permissions"""
    return {
        'can_view_all': user.has_perm('client.view_all_clients') or user.is_superuser,
        'can_assign': user.has_perm('client.assign_client') or user.is_superuser,
        'can_change_stage': user.has_perm('client.change_client_stage') or user.is_superuser,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Login endpoint - returns auth token
    POST: {"email": "...", "password": "..."}
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, email=email, password=password)
    
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token, _ = Token.objects.get_or_create(user=user)
    perms = get_user_permissions(user)
    
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.get_full_name() or user.email,
        },
        'permissions': perms
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clients_api(request):
    """
    Get clients based on user permissions
    - Users with view_all_clients: see all clients
    - Others: see only assigned clients
    """
    user = request.user
    perms = get_user_permissions(user)
    
    if perms['can_view_all']:
        clients_qs = Client.objects.all()
    else:
        clients_qs = Client.objects.filter(
            assignments__assigned_to=user,
            assignments__is_active=True
        ).distinct()
    
    clients_qs = clients_qs.select_related().prefetch_related('assignments__assigned_to')
    
    data = []
    for client in clients_qs:
        active_assignment = client.assignments.filter(is_active=True).first()
        data.append({
            'id': client.id,
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'stage': client.current_stage,
            'stage_display': client.get_current_stage_display(),
            'assigned_to': {
                'id': active_assignment.assigned_to.id,
                'name': active_assignment.assigned_to.get_full_name() or active_assignment.assigned_to.email,
            } if active_assignment and active_assignment.assigned_to else None,
            'context': client.context,
            'created_at': client.created_at.isoformat()
        })
    
    users_for_assign = []
    if perms['can_assign']:
        users_for_assign = [{
            'id': u.id,
            'name': u.get_full_name() or u.email,
            'email': u.email
        } for u in User.objects.filter(is_active=True).exclude(id=user.id)]
    
    return Response({
        'clients': data,
        'permissions': perms,
        'users_for_assign': users_for_assign,
        'stage_choices': dict(Client.STAGE_CHOICES)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_client_api(request):
    """
    Assign client to user
    POST: {"client_id": 1, "user_id": 2}
    """
    user = request.user
    perms = get_user_permissions(user)
    
    if not perms['can_assign']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    client_id = request.data.get('client_id')
    user_id = request.data.get('user_id')
    
    if not client_id or not user_id:
        return Response({'error': 'client_id and user_id required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        assign_to = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
    
    ClientAssignment.objects.create(
        client=client,
        assigned_to=assign_to,
        assigned_by=user,
        is_active=True
    )
    
    return Response({'message': f'Client assigned to {assign_to.get_full_name() or assign_to.email}'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_detail_api(request, client_id):
    """Get client details"""
    user = request.user
    perms = get_user_permissions(user)
    
    if perms['can_view_all']:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        try:
            client = Client.objects.get(
                id=client_id,
                assignments__assigned_to=user,
                assignments__is_active=True
            )
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    
    stage_history = [{
        'from_stage': h.from_stage,
        'to_stage': h.to_stage,
        'changed_by': h.changed_by.get_full_name() if h.changed_by else None,
        'remarks': h.remarks,
        'created_at': h.created_at.isoformat()
    } for h in client.stage_history.select_related('changed_by').all()]
    
    return Response({
        'client': {
            'id': client.id,
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'stage': client.current_stage,
            'stage_display': client.get_current_stage_display(),
            'context': client.context,
            'created_at': client.created_at.isoformat()
        },
        'stage_history': stage_history,
        'permissions': perms,
        'stage_choices': dict(Client.STAGE_CHOICES)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_stage_api(request, client_id):
    """
    Change client stage
    POST: {"new_stage": "contacted", "remarks": "optional"}
    """
    user = request.user
    perms = get_user_permissions(user)
    
    if not perms['can_change_stage']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    if perms['can_view_all']:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        try:
            client = Client.objects.get(
                id=client_id,
                assignments__assigned_to=user,
                assignments__is_active=True
            )
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    
    new_stage = request.data.get('new_stage')
    remarks = request.data.get('remarks', '')
    
    valid_stages = [s[0] for s in Client.STAGE_CHOICES]
    if new_stage not in valid_stages:
        return Response({'error': 'Invalid stage'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_stage != client.current_stage:
        ClientStageHistory.objects.create(
            client=client,
            from_stage=client.current_stage,
            to_stage=new_stage,
            changed_by=user,
            remarks=remarks
        )
        client.current_stage = new_stage
        client.save()
    
    return Response({
        'message': f'Stage updated to {dict(Client.STAGE_CHOICES).get(new_stage)}',
        'stage': new_stage
    })
