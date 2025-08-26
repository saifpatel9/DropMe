from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PromoCode
from .forms import PromoCodeForm
from django.utils.timezone import now

# View all promo codes
def promo_dashboard(request):
    promos = PromoCode.objects.all().order_by('-start_time')
    return render(request, 'promo/promo_dashboard.html', {'promos': promos, 'now': now()})

# Add promo code
def add_promo(request):
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Promo code added successfully.")
            return redirect('promo:promo_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PromoCodeForm()

        print("Form type:", type(form))
    return render(request, 'promo/add_promo.html', {'form': form})

# Edit promo code
def edit_promo(request, promo_id):
    promo = get_object_or_404(PromoCode, promo_id=promo_id)
    if request.method == 'POST':
        form = PromoCodeForm(request.POST, instance=promo)
        if form.is_valid():
            form.save()
            messages.success(request, "Promo code updated successfully.")
            return redirect('promo:promo_dashboard')
    else:
        form = PromoCodeForm(instance=promo)
    return render(request, 'promo/edit_promo.html', {'form': form, 'promo': promo})

# Delete promo code
def delete_promo(request, promo_id):
    promo = get_object_or_404(PromoCode, promo_id=promo_id)
    
    if request.method == 'POST':
        promo.delete()
        messages.warning(request, "Promo code deleted.")
        return redirect('promo:promo_dashboard')

    return render(request, 'promo/confirm_delete_promo.html', {'promo': promo})

