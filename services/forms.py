from .models import FareSlab
from django import forms
from .models import RentalPackage, RentalService, ServiceType


class RentalPackageForm(forms.ModelForm):
    class Meta:
        model = RentalPackage
        fields = ['distance_km', 'time_hours']
        widgets = {
            'distance_km': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-md text-gray-800'
            }),
            'time_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-md text-gray-800'
            }),
        }


class RentalServiceForm(forms.ModelForm):
    class Meta:
        model = RentalService
        fields = [
            'service_type', 'package',
            'base_fare', 'booking_fee',
            'per_km_rate', 'per_minute_rate'
        ]
        widgets = {
            'service_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'package': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'base_fare': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'booking_fee': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'per_km_rate': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'per_minute_rate': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        service_type = cleaned_data.get('service_type')
        package = cleaned_data.get('package')

        if service_type and package:
            existing = RentalService.objects.filter(service_type=service_type, package=package)

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    f"A rental service already exists for {service_type.name} with this package."
                )

        return cleaned_data


# ✅ Add this new form for ServiceType
class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = [
            'name', 'number_of_seats', 'base_fare', 'min_fare', 'booking_fee',
            'tax_percentage', 'price_per_minute', 'price_per_km', 'mileage',
            'daily_service', 'rental_service', 'outstation_service',
            'provider_commission', 'admin_commission', 'driver_cash_limit',
            'picture','status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'number_of_seats': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'base_fare': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'min_fare': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'booking_fee': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'price_per_minute': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'price_per_km': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'mileage': forms.Select(choices=[(1, 'Yes'), (0, 'No')], attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'daily_service': forms.Select(choices=[(1, 'Yes'), (0, 'No')], attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'rental_service': forms.Select(choices=[(1, 'Yes'), (0, 'No')], attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'outstation_service': forms.Select(choices=[(1, 'Yes'), (0, 'No')], attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'provider_commission': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'admin_commission': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'driver_cash_limit': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'picture': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'status': forms.HiddenInput()

        }

# FareSlabForm for FareSlab model
class FareSlabForm(forms.ModelForm):
    class Meta:
        model = FareSlab
        fields = [
            'service_type',
            'km_from', 'km_to',
            'base_fare',
            'rate_per_km',
            'rate_per_minute'
        ]
        widgets = {
            'service_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'km_from': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'km_to': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'base_fare': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'rate_per_km': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
            'rate_per_minute': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md text-gray-800'}),
        }