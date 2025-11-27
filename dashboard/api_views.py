from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from client.models import Client, ClientAssignment, ClientStageHistory
from account.models import User, Role
from .permissions import IsAdmin, IsCSM, IsAdminOrCSM


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
        return Response(
            {'error': 'Email and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, email=email, password=password)
    
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token, _ = Token.objects.get_or_create(user=user)
    
    role_name = user.role.name if user.role else ('admin' if user.is_superuser else None)
    
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.get_full_name() or user.email,
            'role': role_name
        }
    })


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_clients_api(request):
    """
    Admin: Get all clients
    """
    clients = Client.objects.select_related().prefetch_related(
        'assignments__assigned_to'
    ).all()
    
    data = []
    for client in clients:
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
                'email': active_assignment.assigned_to.email
            } if active_assignment and active_assignment.assigned_to else None,
            'created_at': client.created_at.isoformat()
        })
    
    return Response({'clients': data})


@api_view(['POST'])
@permission_classes([IsAdmin])
def assign_client_api(request):
    """
    Admin: Assign client to CSM
    POST: {"client_id": 1, "csm_id": 2}
    """
    client_id = request.data.get('client_id')
    csm_id = request.data.get('csm_id')
    
    if not client_id or not csm_id:
        return Response(
            {'error': 'client_id and csm_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    
    csm_role = Role.objects.filter(name__iexact='csm').first()
    if not csm_role:
        return Response({'error': 'CSM role not configured'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        csm = User.objects.get(id=csm_id, role=csm_role, is_active=True)
    except User.DoesNotExist:
        return Response({'error': 'CSM user not found'}, status=status.HTTP_404_NOT_FOUND)
    
    ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
    
    ClientAssignment.objects.create(
        client=client,
        assigned_to=csm,
        assigned_by=request.user,
        is_active=True
    )
    
    return Response({'message': f'Client assigned to {csm.get_full_name() or csm.email}'})


@api_view(['GET'])
@permission_classes([IsAdmin])
def csm_users_api(request):
    """
    Admin: Get all CSM users for assignment dropdown
    """
    csm_role = Role.objects.filter(name__iexact='csm').first()
    if not csm_role:
        return Response({'csm_users': []})
    
    csm_users = User.objects.filter(role=csm_role, is_active=True)
    data = [{
        'id': u.id,
        'name': u.get_full_name() or u.email,
        'email': u.email
    } for u in csm_users]
    
    return Response({'csm_users': data})


@api_view(['GET'])
@permission_classes([IsCSM])
def csm_clients_api(request):
    """
    CSM: Get assigned clients only
    """
    clients = Client.objects.filter(
        assignments__assigned_to=request.user,
        assignments__is_active=True
    ).distinct()
    
    data = []
    for client in clients:
        data.append({
            'id': client.id,
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'stage': client.current_stage,
            'stage_display': client.get_current_stage_display(),
            'context': client.context,
            'created_at': client.created_at.isoformat()
        })
    
    return Response({'clients': data})


@api_view(['GET'])
@permission_classes([IsAdminOrCSM])
def client_detail_api(request, client_id):
    """
    Get client details (Admin sees all, CSM sees only assigned)
    """
    user = request.user
    is_admin = user.is_superuser or (user.role and user.role.name.lower() == 'admin')
    
    if is_admin:
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
            return Response({'error': 'Client not found or not assigned to you'}, status=status.HTTP_404_NOT_FOUND)
    
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
        'stage_choices': dict(Client.STAGE_CHOICES)
    })


@api_view(['POST'])
@permission_classes([IsAdminOrCSM])
def change_stage_api(request, client_id):
    """
    Change client stage
    POST: {"new_stage": "contacted", "remarks": "optional"}
    """
    user = request.user
    is_admin = user.is_superuser or (user.role and user.role.name.lower() == 'admin')
    
    if is_admin:
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
            return Response({'error': 'Client not found or not assigned to you'}, status=status.HTTP_404_NOT_FOUND)
    
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
