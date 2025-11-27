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
    
    if request.method == 'POST':
        data = request.data
        client = Client.objects.create(
            name=data.get('name'), email=data.get('email'), phone=data.get('phone'),
            session_id=data.get('session_id'), current_stage=data.get('stage', 'lead')
        )
        return Response({'id': client.id}, status=status.HTTP_201_CREATED)
    
    qs = Client.objects.all() if user.can_view_all else Client.objects.filter(assignments__assigned_to=user, assignments__is_active=True).distinct()
    qs = qs.prefetch_related('assignments__assigned_to')
    
    data = []
    for c in qs:
        a = c.assignments.filter(is_active=True).first()
        data.append({
            'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone,
            'stage': c.current_stage, 'assigned_to': a.assigned_to.email if a and a.assigned_to else None,
            'context': c.context
        })
    
    return Response({'clients': data, 'stages': dict(Client.STAGE_CHOICES)})


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def client_detail(request, pk):
    user = request.user
    
    try:
        client = Client.objects.get(pk=pk) if user.can_view_all else Client.objects.get(pk=pk, assignments__assigned_to=user, assignments__is_active=True)
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
        
        if 'stage' in data and data['stage'] != client.current_stage:
            ClientStageHistory.objects.create(client=client, from_stage=client.current_stage, to_stage=data['stage'], changed_by=user)
            client.current_stage = data['stage']
        
        if 'assign_to' in data:
            try:
                assign_to = User.objects.get(pk=data['assign_to'], is_active=True)
                ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
                ClientAssignment.objects.create(client=client, assigned_to=assign_to, assigned_by=user, is_active=True)
            except User.DoesNotExist:
                pass
        
        client.save()
        return Response({'message': 'Updated'})
    
    history = [{'from': h.from_stage, 'to': h.to_stage, 'by': h.changed_by.email if h.changed_by else None, 'at': h.created_at.isoformat()} 
               for h in client.stage_history.select_related('changed_by')]
    
    return Response({
        'client': {'id': client.id, 'name': client.name, 'email': client.email, 'phone': client.phone, 
                   'stage': client.current_stage, 'context': client.context},
        'history': history, 'stages': dict(Client.STAGE_CHOICES)
    })
