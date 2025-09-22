from django import forms
from .models import Driver

class DriverEditProfileForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ["first_name", "last_name", "phone", "state", "city", "full_address"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "state": forms.TextInput(attrs={"class": "form-input"}),
            "city": forms.TextInput(attrs={"class": "form-input"}),
            "full_address": forms.Textarea(attrs={"class": "form-input h-24"}),
        }


class RideRequestFilterForm(forms.Form):
    """Minimal stub for future ride request filters."""
    status = forms.ChoiceField(
        choices=[('all', 'All')],
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )