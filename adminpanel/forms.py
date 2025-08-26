from django import forms
from passenger.models import User
from driver.models import Driver
from services.models import RentalService


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


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = '__all__' # Includes all fields from the Driver model
        
        widgets = {
            'password_hash': forms.PasswordInput(),
            'full_address': forms.Textarea(attrs={'rows': 3}),
            'manufacturing_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'e.g., +919876543210'}),
            'rating': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '5'}),
            # 'created_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}), # Uncomment if you want to allow manual input
        }

        labels = {
            'upi_id': 'UPI ID',
            'ifsc_code': 'IFSC Code',
            'vehicle_rc': 'Vehicle RC Document',
        }
        help_texts = {
            'phone': 'Enter phone number with country code, e.g., +919876543210',
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