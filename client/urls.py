from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    path('', views.clients, name='list'),
    path('<int:pk>/', views.client_detail, name='detail'),
]
