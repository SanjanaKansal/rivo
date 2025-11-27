from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    path('', views.clients_list, name='list'),
    path('assign/', views.assign_client, name='assign'),
    path('<int:client_id>/', views.client_detail, name='detail'),
    path('<int:client_id>/stage/', views.change_stage, name='change_stage'),
]
