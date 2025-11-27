from django.urls import path
from . import api_views

urlpatterns = [
    path('login/', api_views.login_api, name='api_login'),
    path('clients/', api_views.clients_api, name='api_clients'),
    path('assign/', api_views.assign_client_api, name='api_assign'),
    path('client/<int:client_id>/', api_views.client_detail_api, name='api_client_detail'),
    path('client/<int:client_id>/stage/', api_views.change_stage_api, name='api_change_stage'),
]
