from django import forms
from .models import User
from django.core.exceptions import ValidationError

class SignupForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'password', 
            'gender', 'referral_code', 'country_code'
        ]
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'referral_code': 'Referral Code (Optional)',
        }

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['country_code'].initial = '+91'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Passwords do not match.")

    def save(self, commit=True):
        user = super().save(commit=False)
        from django.contrib.auth.hashers import make_password
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

from django import forms
from .models import User

class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["emergency_contact"]
        widgets = {
            "emergency_contact": forms.TextInput(
                attrs={
                    "placeholder": "Enter emergency contact number",
                    "class": "pl-10 block w-full px-4 py-3 border-2 border-gray-200 rounded-xl shadow-sm "
                             "focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent "
                             "transition-all duration-300 bg-white"
                }
            )
        }

class PaymentMethodForm(forms.ModelForm):
    # Updated choices to match template expectations
    PAYMENT_CHOICES = [
        ("Cash", "Cash"),
        ("Credit Card", "Credit Card"),
        ("Debit Card", "Debit Card"),
        ("Digital Wallet", "Digital Wallet"),
        ("UPI", "UPI"),
        ("Net Banking", "Net Banking"),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "sr-only"}),
        required=True
    )

    class Meta:
        model = User
        fields = ["payment_method"]