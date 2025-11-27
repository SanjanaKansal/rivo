from django.urls import path
from . import api_views

urlpatterns = [
    path('login/', api_views.login_api, name='api_login'),
    
    path('admin/clients/', api_views.admin_clients_api, name='api_admin_clients'),
    path('admin/csm-users/', api_views.csm_users_api, name='api_csm_users'),
    path('admin/assign/', api_views.assign_client_api, name='api_assign_client'),
    
    path('csm/clients/', api_views.csm_clients_api, name='api_csm_clients'),
    
    path('client/<int:client_id>/', api_views.client_detail_api, name='api_client_detail'),
    path('client/<int:client_id>/stage/', api_views.change_stage_api, name='api_change_stage'),
]
