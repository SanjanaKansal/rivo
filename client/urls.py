from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    path('', views.clients_list, name='list'),
    path('<int:client_id>/', views.client_detail, name='detail'),
]
