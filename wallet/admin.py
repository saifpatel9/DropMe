from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('wallet_id', 'user', 'total_amount', 'used_amount', 'remaining_amount', 'last_updated')