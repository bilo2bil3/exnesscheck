from django.contrib import admin
from .models import ClientValidation

@admin.register(ClientValidation)
class ClientValidationAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'is_registered', 'client_account', 'client_account_type', 'volume_lots', 'reward_usd', 'created_at')
    list_filter = ('is_registered', 'client_account_type')
    search_fields = ('client_id', 'client_account')
    readonly_fields = ('created_at',) 