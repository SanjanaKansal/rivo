from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Client, ClientAssignment, ClientStageHistory
from account.models import User


def get_user_permissions(user):
    return {
        'can_view_all': user.has_perm('client.view_all_clients') or user.is_superuser,
        'can_assign': user.has_perm('client.assign_client') or user.is_superuser,
        'can_change_stage': user.has_perm('client.change_client_stage') or user.is_superuser,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clients_list(request):
    user = request.user
    perms = get_user_permissions(user)
    
    if request.method == 'POST':
        data = request.data
        client = Client.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            session_id=data.get('session_id'),
            current_stage=data.get('stage', 'lead')
        )
        return Response({'id': client.id, 'message': 'Client created'}, status=status.HTTP_201_CREATED)
    
    if perms['can_view_all']:
        clients_qs = Client.objects.all()
    else:
        clients_qs = Client.objects.filter(
            assignments__assigned_to=user,
            assignments__is_active=True
        ).distinct()
    
    clients_qs = clients_qs.prefetch_related('assignments__assigned_to')
    
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
        users_for_assign = [{'id': u.id, 'name': u.get_full_name() or u.email} 
                           for u in User.objects.filter(is_active=True).exclude(id=user.id)]
    
    return Response({
        'clients': data,
        'permissions': perms,
        'users_for_assign': users_for_assign,
        'stage_choices': dict(Client.STAGE_CHOICES)
    })


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def client_detail(request, client_id):
    user = request.user
    perms = get_user_permissions(user)
    
    if perms['can_view_all']:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        try:
            client = Client.objects.get(id=client_id, assignments__assigned_to=user, assignments__is_active=True)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'DELETE':
        client.delete()
        return Response({'message': 'Client deleted'})
    
    if request.method == 'PUT':
        data = request.data
        
        if 'name' in data:
            client.name = data['name']
        if 'email' in data:
            client.email = data['email']
        if 'phone' in data:
            client.phone = data['phone']
        
        if 'stage' in data and perms['can_change_stage']:
            new_stage = data['stage']
            if new_stage != client.current_stage:
                ClientStageHistory.objects.create(
                    client=client,
                    from_stage=client.current_stage,
                    to_stage=new_stage,
                    changed_by=user,
                    remarks=data.get('remarks', '')
                )
                client.current_stage = new_stage
        
        if 'assign_to' in data and perms['can_assign']:
            try:
                assign_to = User.objects.get(id=data['assign_to'], is_active=True)
                ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
                ClientAssignment.objects.create(client=client, assigned_to=assign_to, assigned_by=user, is_active=True)
            except User.DoesNotExist:
                pass
        
        client.save()
        return Response({'message': 'Client updated'})
    
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
