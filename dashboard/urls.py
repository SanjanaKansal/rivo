from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('assign/', views.assign_client, name='assign_client'),
    path('client/<int:client_id>/', views.client_detail, name='client_detail'),
]
