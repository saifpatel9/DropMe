from django.shortcuts import render
from .models import Wallet

def wallet_dashboard(request):
    wallets = Wallet.objects.select_related('user').all()
    return render(request, 'wallet/wallet_dashboard.html', {
        'wallets': wallets,
    })