from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['manufacturer', 'color', 'model_name', 'manufacturing_year', 'seat_arrangement']
        widgets = {
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2100}),
            'seat_arrangement': forms.NumberInput(attrs={'class': 'form-control'}),
        }