from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Client, ClientAssignment, ClientStageHistory
from account.models import User


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clients(request):
    user = request.user
    perms = user.get_permissions()
    
    if request.method == 'POST':
        data = request.data
        client = Client.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            session_id=data.get('session_id'),
            current_stage=data.get('stage', 'lead')
        )
        return Response({'id': client.id}, status=status.HTTP_201_CREATED)
    
    if perms['can_view_all']:
        qs = Client.objects.all()
    else:
        qs = Client.objects.filter(assignments__assigned_to=user, assignments__is_active=True).distinct()
    
    qs = qs.prefetch_related('assignments__assigned_to')
    
    data = []
    for c in qs:
        assignment = c.assignments.filter(is_active=True).first()
        data.append({
            'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone,
            'stage': c.current_stage, 'stage_display': c.get_current_stage_display(),
            'assigned_to': {'id': assignment.assigned_to.id, 'name': assignment.assigned_to.get_full_name() or assignment.assigned_to.email} if assignment and assignment.assigned_to else None,
            'context': c.context, 'created_at': c.created_at.isoformat()
        })
    
    users = [{'id': u.id, 'name': u.get_full_name() or u.email} for u in User.objects.filter(is_active=True).exclude(id=user.id)] if perms['can_assign'] else []
    
    return Response({'clients': data, 'permissions': perms, 'users': users, 'stages': dict(Client.STAGE_CHOICES)})


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def client_detail(request, pk):
    user = request.user
    perms = user.get_permissions()
    
    try:
        if perms['can_view_all']:
            client = Client.objects.get(pk=pk)
        else:
            client = Client.objects.get(pk=pk, assignments__assigned_to=user, assignments__is_active=True)
    except Client.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'DELETE':
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    if request.method == 'PUT':
        data = request.data
        for field in ['name', 'email', 'phone']:
            if field in data:
                setattr(client, field, data[field])
        
        if 'stage' in data and perms['can_change_stage'] and data['stage'] != client.current_stage:
            ClientStageHistory.objects.create(client=client, from_stage=client.current_stage, to_stage=data['stage'], changed_by=user)
            client.current_stage = data['stage']
        
        if 'assign_to' in data and perms['can_assign']:
            try:
                assign_to = User.objects.get(pk=data['assign_to'], is_active=True)
                ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
                ClientAssignment.objects.create(client=client, assigned_to=assign_to, assigned_by=user, is_active=True)
            except User.DoesNotExist:
                pass
        
        client.save()
        return Response({'message': 'Updated'})
    
    history = [{'from': h.from_stage, 'to': h.to_stage, 'by': h.changed_by.get_full_name() if h.changed_by else None, 'at': h.created_at.isoformat()} 
               for h in client.stage_history.select_related('changed_by')]
    
    return Response({
        'client': {'id': client.id, 'name': client.name, 'email': client.email, 'phone': client.phone, 
                   'stage': client.current_stage, 'context': client.context, 'created_at': client.created_at.isoformat()},
        'history': history, 'permissions': perms, 'stages': dict(Client.STAGE_CHOICES)
    })
