from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('csm/', views.csm_dashboard, name='csm_dashboard'),
    path('client/<int:client_id>/', views.client_detail, name='client_detail'),
]
