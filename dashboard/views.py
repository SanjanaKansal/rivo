from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from client.models import Client, ClientAssignment, ClientStageHistory
from account.models import User, Role
from .forms import LoginForm, ClientAssignmentForm, StageChangeForm


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


@login_required
def home_view(request):
    user = request.user
    is_admin = user.is_superuser or (user.role and user.role.name.lower() == 'admin')
    
    if is_admin:
        return redirect('dashboard:admin_dashboard')
    else:
        return redirect('dashboard:csm_dashboard')


@login_required
def admin_dashboard(request):
    user = request.user
    is_admin = user.is_superuser or (user.role and user.role.name.lower() == 'admin')
    
    if not is_admin:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard:csm_dashboard')
    
    clients = Client.objects.select_related().prefetch_related(
        'assignments__assigned_to'
    ).all()
    
    csm_role = Role.objects.filter(name__iexact='csm').first()
    csm_users = User.objects.filter(role=csm_role, is_active=True) if csm_role else User.objects.filter(is_active=True)
    
    unassigned_clients = clients.filter(
        Q(assignments__isnull=True) | Q(assignments__is_active=False)
    ).distinct()
    
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        csm_id = request.POST.get('csm_id')
        
        if client_id and csm_id:
            client = get_object_or_404(Client, id=client_id)
            csm = get_object_or_404(User, id=csm_id)
            
            ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
            
            ClientAssignment.objects.create(
                client=client,
                assigned_to=csm,
                assigned_by=user,
                is_active=True
            )
            messages.success(request, f'Client {client.name} assigned to {csm.get_full_name() or csm.email}')
            return redirect('dashboard:admin_dashboard')
    
    context = {
        'clients': clients,
        'csm_users': csm_users,
        'unassigned_clients': unassigned_clients,
        'is_admin': True,
        'stage_choices': Client.STAGE_CHOICES,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def csm_dashboard(request):
    user = request.user
    
    assigned_clients = Client.objects.filter(
        assignments__assigned_to=user,
        assignments__is_active=True
    ).select_related().prefetch_related('stage_history').distinct()
    
    context = {
        'clients': assigned_clients,
        'is_admin': False,
        'stage_choices': Client.STAGE_CHOICES,
    }
    return render(request, 'dashboard/csm_dashboard.html', context)


@login_required
def client_detail(request, client_id):
    user = request.user
    is_admin = user.is_superuser or (user.role and user.role.name.lower() == 'admin')
    
    if is_admin:
        client = get_object_or_404(Client, id=client_id)
    else:
        client = get_object_or_404(
            Client,
            id=client_id,
            assignments__assigned_to=user,
            assignments__is_active=True
        )
    
    stage_history = client.stage_history.select_related('changed_by').all()
    
    if request.method == 'POST':
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
        'is_admin': is_admin,
        'stage_choices': Client.STAGE_CHOICES,
    }
    return render(request, 'dashboard/client_detail.html', context)
