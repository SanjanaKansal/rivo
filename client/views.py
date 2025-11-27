from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Client
from account.models import User


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clients(request):
    if request.method == 'POST':
        data = request.data
        client = Client.objects.create(
            name=data.get('name'), email=data.get('email'), phone=data.get('phone'),
            current_stage=data.get('stage', 'lead')
        )
        return Response({'id': client.id}, status=status.HTTP_201_CREATED)
    
    data = []
    for c in Client.objects.all().prefetch_related('assignments__assigned_to'):
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
    try:
        client = Client.objects.get(pk=pk)
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
        client.save()
        
        if 'stage' in data:
            client.set_stage(data['stage'], changed_by=request.user)
        
        if 'assign_to' in data:
            try:
                assign_to = User.objects.get(pk=data['assign_to'], is_active=True)
                client.assign(assigned_to=assign_to, assigned_by=request.user)
            except User.DoesNotExist:
                pass
        
        return Response({'message': 'Updated'})
    
    history = [{'from': h.from_stage, 'to': h.to_stage, 'by': h.changed_by.email if h.changed_by else None, 'at': h.created_at.isoformat()} 
               for h in client.stage_history.select_related('changed_by')]
    
    return Response({
        'client': {'id': client.id, 'name': client.name, 'email': client.email, 'phone': client.phone, 
                   'stage': client.current_stage, 'context': client.context},
        'history': history, 'stages': dict(Client.STAGE_CHOICES)
    })
