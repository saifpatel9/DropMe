from django import forms
from passenger.models import User
from driver.models import Driver
from services.models import RentalService
from config.validators import MOBILE_NUMBER_ERROR, MOBILE_NUMBER_PATTERN, mobile_number_validator


class PassengerForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'country_code',
            'gender', 'description', 'payment_method', 'is_verified',
            'status', 'referral_code', 'referred_by'
        ]
        widgets = {
            'is_verified': forms.Select(choices=[
                (True, 'Yes'),
                (False, 'No'),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super(PassengerForm, self).__init__(*args, **kwargs)
        input_class = 'w-full h-[50px] px-4 text-base font-body border border-gray-300 rounded-md bg-white text-gray-800'

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-checkbox h-5 w-5 text-primary'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': input_class, 'style': 'height: 100px; resize: vertical;'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': input_class})
            else:
                field.widget.attrs.update({'class': input_class})

        if 'phone' in self.fields:
            self.fields['phone'].widget.attrs.update({
                'pattern': MOBILE_NUMBER_PATTERN,
                'maxlength': '10',
                'inputmode': 'numeric',
                'title': MOBILE_NUMBER_ERROR,
            })

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        mobile_number_validator(phone)
        return phone


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = '__all__' # Includes all fields from the Driver model
        
        widgets = {
            'password_hash': forms.PasswordInput(),
            'full_address': forms.Textarea(attrs={'rows': 3}),
            'manufacturing_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter 10-digit mobile number'}),
            'rating': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '5'}),
            # 'created_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}), # Uncomment if you want to allow manual input
        }

        labels = {
            'upi_id': 'UPI ID',
            'ifsc_code': 'IFSC Code',
            'vehicle_rc': 'Vehicle RC Document',
        }
        help_texts = {
            'phone': MOBILE_NUMBER_ERROR,
            'availability': '0 for Unavailable, 1 for Available',
            'password_hash': 'Driver password will be hashed securely.',
        }

    def __init__(self, *args, **kwargs):
        super(DriverForm, self).__init__(*args, **kwargs)
        input_class = 'w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-teal-500'

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-checkbox h-5 w-5 text-primary'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': input_class, 'style': 'height: 100px; resize: vertical;'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': input_class})
            else:
                field.widget.attrs.update({'class': input_class})

        # Enforce required fields (backend safety)
        required_fields = [
            'first_name', 'last_name', 'phone', 'email',
            'full_address', 'vehicle_type', 'plate_number',
            'manufacturer', 'license_document'
        ]
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True
        # Prefer numeric phone and length hint
        if 'phone' in self.fields:
            self.fields['phone'].widget.attrs.update({
                'pattern': MOBILE_NUMBER_PATTERN,
                'maxlength': '10',
                'inputmode': 'numeric',
                'title': MOBILE_NUMBER_ERROR,
            })

    def clean(self):
        cleaned = super().clean()
        errors = {}

        # Required checks (defensive even if widget required)
        def require(field, label=None):
            if not cleaned.get(field):
                errors[field] = f"{label or field.replace('_', ' ').title()} is required."

        require('first_name', 'First name')
        require('last_name', 'Last name')
        require('phone', 'Mobile number')
        require('email', 'Email')
        require('full_address', 'Address')
        require('vehicle_type', 'Vehicle type')
        require('plate_number', 'Vehicle number')
        require('manufacturer', 'Vehicle model')
        require('license_document', 'License document')

        # Phone format: 10 digits
        phone = cleaned.get('phone') or ''
        if phone:
            try:
                mobile_number_validator(phone)
            except forms.ValidationError:
                errors['phone'] = MOBILE_NUMBER_ERROR

        # If any errors, raise
        if errors:
            for field, msg in errors.items():
                self.add_error(field, msg)
        return cleaned

class RentalServiceForm(forms.ModelForm):
    class Meta:
        model = RentalService
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        service_type = cleaned_data.get('service_type')
        package = cleaned_data.get('package')

        if service_type and package:
            # Check for existing combination
            if RentalService.objects.filter(service_type=service_type, package=package).exists():
                raise forms.ValidationError(
                    f"A rental service already exists for '{service_type}' with package '{package}'."
                )
            
# adminpanel/forms.py
from django import forms
from faq.models import FAQ, MainTopic, SubTopic

class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['main_topic', 'sub_topic', 'question', 'answer']
        widgets = {
            'main_topic': forms.Select(attrs={'class': 'form-input'}),
            'sub_topic': forms.Select(attrs={'class': 'form-input'}),
            'question': forms.TextInput(attrs={'class': 'form-input'}),
            'answer': forms.Textarea(attrs={'class': 'form-textarea'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sub_topic'].queryset = SubTopic.objects.none()

        if 'main_topic' in self.data:
            try:
                main_topic_id = int(self.data.get('main_topic'))
                self.fields['sub_topic'].queryset = SubTopic.objects.filter(main_topic_id=main_topic_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['sub_topic'].queryset = self.instance.main_topic.subtopic_set.all()
