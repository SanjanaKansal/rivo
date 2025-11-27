from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from client.models import Client
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
    clients = []
    
    for c in Client.objects.all().prefetch_related('assignments__assigned_to'):
        a = c.assignments.filter(is_active=True).first()
        c.active_csm = a.assigned_to if a else None  # type: ignore
        clients.append(c)
    
    csm_users = User.objects.filter(is_active=True).exclude(id=user.id) if user.can_change_client else []
    
    return render(request, 'dashboard/dashboard.html', {
        'clients': clients, 'csm_users': csm_users, 
        'perms': {'can_change_client': user.can_change_client},
        'stage_choices': Client.STAGE_CHOICES
    })


@login_required
def assign_client(request):
    if request.method != 'POST' or not request.user.can_change_client:
        return redirect('dashboard:home')
    
    client_id, user_id = request.POST.get('client_id'), request.POST.get('user_id')
    if client_id and user_id:
        client = get_object_or_404(Client, id=client_id)
        csm = get_object_or_404(User, id=user_id, is_active=True)
        client.assign(assigned_to=csm, assigned_by=request.user)
    
    return redirect('dashboard:home')


@login_required
def client_detail(request, client_id):
    user = request.user
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST' and user.can_change_client:
        form = StageChangeForm(request.POST)
        if form.is_valid():
            client.set_stage(form.cleaned_data['new_stage'], changed_by=user)
            return redirect('dashboard:client_detail', client_id=client_id)
    else:
        form = StageChangeForm(initial={'new_stage': client.current_stage})
    
    return render(request, 'dashboard/client_detail.html', {
        'client': client, 'stage_history': client.stage_history.all(),
        'perms': {'can_change_client': user.can_change_client}, 'form': form
    })
