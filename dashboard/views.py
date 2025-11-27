from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from client.models import Client, ClientAssignment, ClientStageHistory
from account.models import User
from .forms import LoginForm, StageChangeForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('dashboard:home')
    else:
        form = LoginForm()
    return render(request, 'dashboard/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('dashboard:login')


@login_required
def home_view(request):
    user = request.user
    
    qs = Client.objects.all() if user.can_view_all else Client.objects.filter(assignments__assigned_to=user, assignments__is_active=True).distinct()
    qs = qs.prefetch_related('assignments__assigned_to')
    
    clients = []
    for c in qs:
        a = c.assignments.filter(is_active=True).first()
        c.active_csm = a.assigned_to if a else None
        clients.append(c)
    
    csm_users = User.objects.filter(is_active=True).exclude(id=user.id) if user.can_assign else []
    
    return render(request, 'dashboard/dashboard.html', {
        'clients': clients, 'csm_users': csm_users, 
        'perms': {'can_assign': user.can_assign, 'can_change_stage': user.can_change_stage},
        'stage_choices': Client.STAGE_CHOICES
    })


@login_required
def assign_client(request):
    if request.method != 'POST' or not request.user.can_assign:
        return redirect('dashboard:home')
    
    client_id, user_id = request.POST.get('client_id'), request.POST.get('user_id')
    if client_id and user_id:
        client = get_object_or_404(Client, id=client_id)
        csm = get_object_or_404(User, id=user_id, is_active=True)
        ClientAssignment.objects.filter(client=client, is_active=True).update(is_active=False)
        ClientAssignment.objects.create(client=client, assigned_to=csm, assigned_by=request.user, is_active=True)
    
    return redirect('dashboard:home')


@login_required
def client_detail(request, client_id):
    user = request.user
    
    client = get_object_or_404(Client, id=client_id) if user.can_view_all else get_object_or_404(Client, id=client_id, assignments__assigned_to=user, assignments__is_active=True)
    
    if request.method == 'POST':
        form = StageChangeForm(request.POST)
        if form.is_valid() and form.cleaned_data['new_stage'] != client.current_stage:
            ClientStageHistory.objects.create(client=client, from_stage=client.current_stage, to_stage=form.cleaned_data['new_stage'], changed_by=user)
            client.current_stage = form.cleaned_data['new_stage']
            client.save()
            return redirect('dashboard:client_detail', client_id=client_id)
    else:
        form = StageChangeForm(initial={'new_stage': client.current_stage})
    
    return render(request, 'dashboard/client_detail.html', {
        'client': client, 'stage_history': client.stage_history.select_related('changed_by'), 'form': form,
        'perms': {'can_change_stage': user.can_change_stage}
    })
