from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from client.models import Client, ClientAssignment, ClientStageHistory
from account.models import User, Role
from .forms import LoginForm, StageChangeForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Invalid email or password')
    else:
        form = LoginForm()
    
    return render(request, 'dashboard/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('dashboard:login')


def get_user_permissions(user):
    """Get user's dashboard permissions"""
    return {
        'can_view_all': user.has_perm('client.view_all_clients') or user.is_superuser,
        'can_assign': user.has_perm('client.assign_client') or user.is_superuser,
        'can_change_stage': user.has_perm('client.change_client_stage') or user.is_superuser,
    }


@login_required
def home_view(request):
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
    
    clients = []
    for client in clients_qs:
        active_assignment = client.assignments.filter(is_active=True).first()
        client.active_csm = active_assignment.assigned_to if active_assignment else None
        clients.append(client)
    
    csm_users = []
    if perms['can_assign']:
        csm_users = User.objects.filter(is_active=True).exclude(id=user.id)
    
    context = {
        'clients': clients,
        'csm_users': csm_users,
        'perms': perms,
        'stage_choices': Client.STAGE_CHOICES,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def assign_client(request):
    if request.method != 'POST':
        return redirect('dashboard:home')
    
    user = request.user
    perms = get_user_permissions(user)
    
    if not perms['can_assign']:
        messages.error(request, 'Permission denied')
        return redirect('dashboard:home')
    
    client_id = request.POST.get('client_id')
    user_id = request.POST.get('user_id')
    
    if client_id and user_id:
        client = get_object_or_404(Client, id=client_id)
        csm = get_object_or_404(User, id=user_id, is_active=True)
        
        ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
        
        ClientAssignment.objects.create(
            client=client,
            assigned_to=csm,
            assigned_by=user,
            is_active=True
        )
        messages.success(request, f'Client assigned to {csm.get_full_name() or csm.email}')
    
    return redirect('dashboard:home')


@login_required
def client_detail(request, client_id):
    user = request.user
    perms = get_user_permissions(user)
    
    if perms['can_view_all']:
        client = get_object_or_404(Client, id=client_id)
    else:
        client = get_object_or_404(
            Client,
            id=client_id,
            assignments__assigned_to=user,
            assignments__is_active=True
        )
    
    stage_history = client.stage_history.select_related('changed_by').all()
    
    if request.method == 'POST' and perms['can_change_stage']:
        form = StageChangeForm(request.POST)
        if form.is_valid():
            new_stage = form.cleaned_data['new_stage']
            remarks = form.cleaned_data['remarks']
            
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
                messages.success(request, f'Stage updated to {dict(Client.STAGE_CHOICES).get(new_stage)}')
                return redirect('dashboard:client_detail', client_id=client_id)
    else:
        form = StageChangeForm(initial={'new_stage': client.current_stage})
    
    context = {
        'client': client,
        'stage_history': stage_history,
        'form': form,
        'perms': perms,
        'stage_choices': Client.STAGE_CHOICES,
    }
    return render(request, 'dashboard/client_detail.html', context)
