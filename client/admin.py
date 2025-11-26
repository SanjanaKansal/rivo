from django.contrib import admin
from .models import Client, ClientContext, ClientStageHistory, ClientAssignment


class ClientContextInline(admin.StackedInline):
    model = ClientContext
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


class ClientStageHistoryInline(admin.TabularInline):
    model = ClientStageHistory
    extra = 0
    readonly_fields = ['from_stage', 'to_stage', 'changed_by', 'remarks', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ClientAssignmentInline(admin.TabularInline):
    model = ClientAssignment
    extra = 0
    readonly_fields = ['created_at']
    fk_name = 'client'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'current_stage', 'created_at']
    list_filter = ['current_stage', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [ClientContextInline, ClientStageHistoryInline, ClientAssignmentInline]


@admin.register(ClientContext)
class ClientContextAdmin(admin.ModelAdmin):
    list_display = ['client', 'chat_session_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['client__name', 'chat_session_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ClientStageHistory)
class ClientStageHistoryAdmin(admin.ModelAdmin):
    list_display = ['client', 'from_stage', 'to_stage', 'changed_by', 'created_at']
    list_filter = ['from_stage', 'to_stage', 'created_at']
    search_fields = ['client__name', 'remarks']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ClientAssignment)
class ClientAssignmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'assigned_to', 'assigned_by', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['client__name', 'assigned_to__email', 'remarks']
    readonly_fields = ['created_at', 'updated_at']
