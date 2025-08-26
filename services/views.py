from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import RentalPackage, RentalService
from .forms import RentalPackageForm, RentalServiceForm


def rental_dashboard(request):
    packages = RentalPackage.objects.all()
    services = RentalService.objects.select_related('service_type', 'package').all()
    return render(request, 'adminpanel/rental_dashboard.html', {
        'packages': packages,
        'services': services,
    })


def add_rental_package(request):
    if request.method == 'POST':
        form = RentalPackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Rental package added successfully.")
            return redirect('rental_dashboard')
    else:
        form = RentalPackageForm()
    return render(request, 'adminpanel/add_rental_package.html', {'form': form})


def edit_rental_package(request, pk):
    package = get_object_or_404(RentalPackage, pk=pk)
    if request.method == 'POST':
        form = RentalPackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, "Rental package updated successfully.")
            return redirect('rental_dashboard')
    else:
        form = RentalPackageForm(instance=package)
    return render(request, 'adminpanel/edit_rental_package.html', {'form': form})


def delete_rental_package(request, pk):
    package = get_object_or_404(RentalPackage, pk=pk)
    if request.method == 'POST':
        package.delete()
        messages.success(request, "Rental package deleted successfully.")
        return redirect('rental_dashboard')
    return render(request, 'adminpanel/confirm_delete_package.html', {'object': package})


def add_rental_service(request):
    if request.method == 'POST':
        form = RentalServiceForm(request.POST)
        if form.is_valid():
            if RentalService.objects.filter(service_type=form.cleaned_data['service_type'], package=form.cleaned_data['package']).exists():
                form.add_error(None, "A rental service for this service type and package already exists.")
            else:
                form.save()
                messages.success(request, "Rental service added successfully.")
                return redirect('rental_dashboard')
    else:
        form = RentalServiceForm()
    return render(request, 'adminpanel/add_rental_service.html', {'form': form})


def edit_rental_service(request, pk):
    service = get_object_or_404(RentalService, pk=pk)
    if request.method == 'POST':
        form = RentalServiceForm(request.POST, instance=service)
        if form.is_valid():
            existing = RentalService.objects.filter(
                service_type=form.cleaned_data['service_type'],
                package=form.cleaned_data['package']
            ).exclude(pk=service.pk)
            if existing.exists():
                form.add_error(None, "Another rental service for this combination already exists.")
            else:
                form.save()
                messages.success(request, "Rental service updated successfully.")
                return redirect('rental_dashboard')
    else:
        form = RentalServiceForm(instance=service)
    return render(request, 'adminpanel/edit_rental_service.html', {'form': form})


def delete_rental_service(request, pk):
    service = get_object_or_404(RentalService, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Rental service deleted successfully.")
        return redirect('rental_dashboard')
    return render(request, 'adminpanel/confirm_delete_service.html', {'object': service})
