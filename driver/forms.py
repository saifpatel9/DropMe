from django import forms
from .models import Driver
from config.validators import MOBILE_NUMBER_ERROR, MOBILE_NUMBER_PATTERN, mobile_number_validator

class DriverEditProfileForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ["first_name", "last_name", "phone", "state", "city", "full_address"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "pattern": MOBILE_NUMBER_PATTERN,
                    "maxlength": "10",
                    "inputmode": "numeric",
                    "title": MOBILE_NUMBER_ERROR,
                }
            ),
            "state": forms.TextInput(attrs={"class": "form-input"}),
            "city": forms.TextInput(attrs={"class": "form-input"}),
            "full_address": forms.Textarea(attrs={"class": "form-input h-24"}),
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        mobile_number_validator(phone)
        return phone


class RideRequestFilterForm(forms.Form):
    """Minimal stub for future ride request filters."""
    status = forms.ChoiceField(
        choices=[('all', 'All')],
        required=False,
        widget=forms.Select(attrs={'class': 'border rounded px-3 py-2'})
    )
