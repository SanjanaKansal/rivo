from django.contrib import admin
from .models import Client, ClientStageHistory, ClientAssignment


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'current_stage', 'created_at']
    list_filter = ['current_stage', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['context', 'created_at', 'updated_at']


@admin.register(ClientStageHistory)
class ClientStageHistoryAdmin(admin.ModelAdmin):
    list_display = ['client', 'from_stage', 'to_stage', 'changed_by', 'created_at']
    list_filter = ['to_stage', 'created_at']
    search_fields = ['client__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ClientAssignment)
class ClientAssignmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'assigned_to', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['client__name', 'assigned_to__email']
    readonly_fields = ['created_at', 'updated_at']
