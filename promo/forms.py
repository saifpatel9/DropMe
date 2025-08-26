from django import forms
from .models import PromoCode

TAILWIND_INPUT_CLASS = 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'

class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = [
            'code', 'discount_amount', 'start_time', 'expiry_time',
            'description', 'max_usage', 'max_usage_per_user', 'type', 'percentage_value'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'placeholder': 'PROMO2025'
            }),
            'discount_amount': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': TAILWIND_INPUT_CLASS
            }),
            'expiry_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': TAILWIND_INPUT_CLASS
            }),
            'description': forms.Textarea(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'rows': 3
            }),
            'max_usage': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'max_usage_per_user': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS}),
            'type': forms.Select(attrs={'class': TAILWIND_INPUT_CLASS}),
            'percentage_value': forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS})
        }