from django import forms
from users.models import CustomUser
from .models import Property, Unit, Announcement, Invoice, Ticket, ShortTermStay, MeterReading, Expense, PaymentConfiguration

class CheckInForm(forms.ModelForm):
    unit_number = forms.CharField(max_length=20, label="Unit Number", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A-104'}))
    class Meta:
        model = ShortTermStay
        fields = ['guest_name', 'guest_id_number', 'guest_phone', 'id_passport_image']
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guest_id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'guest_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'id_passport_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    def clean_unit_number(self):
        unit_num = self.cleaned_data.get('unit_number')
        unit = Unit.objects.filter(unit_number__iexact=unit_num).first()
        if not unit: raise forms.ValidationError(f"Unit '{unit_num}' does not exist.")
        return unit

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = ShortTermStay
        fields = ['feedback_rating', 'feedback_comment']
        widgets = {
            'feedback_rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-select'}),
            'feedback_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# --- NEW FINANCE FORMS ---

class MeterReadingForm(forms.ModelForm):
    unit_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit No.'}))
    
    class Meta:
        model = MeterReading
        fields = ['current_reading', 'reading_image']
        widgets = {
            'current_reading': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reading_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        unit_num = cleaned_data.get('unit_number')
        current = cleaned_data.get('current_reading')
        
        unit = Unit.objects.filter(unit_number__iexact=unit_num).first()
        if not unit:
            raise forms.ValidationError("Unit not found.")
            
        # Get Previous Reading
        last_reading = MeterReading.objects.filter(meter__unit=unit).order_by('-date_recorded').first()
        if last_reading and current < last_reading.current_reading:
            raise forms.ValidationError(f"Current reading ({current}) cannot be lower than previous ({last_reading.current_reading}).")
            
        cleaned_data['unit'] = unit # Pass to view
        cleaned_data['previous_reading'] = last_reading.current_reading if last_reading else 0
        return cleaned_data

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'payee', 'amount', 'date_incurred', 'description', 'receipt_image']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'payee': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_incurred': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'receipt_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PaymentConfigForm(forms.ModelForm):
    class Meta:
        model = PaymentConfiguration
        fields = ['paybill_number', 'business_shortcode', 'consumer_key', 'consumer_secret', 'passkey']
        widgets = {
            'paybill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'business_shortcode': forms.TextInput(attrs={'class': 'form-control'}),
            'consumer_key': forms.TextInput(attrs={'class': 'form-control'}),
            'consumer_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
            'passkey': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

# --- NEW PM OPERATIONS FORMS ---

class PMUserCreationForm(forms.ModelForm):
    """Form for PM to add new users (Tenants, Landlords, Staff)"""
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

class PropertyCreationForm(forms.ModelForm):
    """Form for PM to add a new Property"""
    class Meta:
        model = Property
        fields = ['name', 'address', 'blocks', 'water_unit_cost', 'electricity_unit_cost']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'blocks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Block A, Block B'}),
            'water_unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'electricity_unit_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AnnouncementForm(forms.ModelForm):
    """Form for PM to post announcements"""
    class Meta:
        model = Announcement
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InvoiceCreationForm(forms.ModelForm):
    """Form for PM to create a manual invoice"""
    unit_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit No.'}))
    
    class Meta:
        model = Invoice
        fields = ['amount', 'due_date', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_unit_number(self):
        unit_num = self.cleaned_data.get('unit_number')
        unit = Unit.objects.filter(unit_number__iexact=unit_num).first()
        if not unit: raise forms.ValidationError("Unit not found.")
        return unit

class UnitCreationForm(forms.ModelForm):
    class Meta:
        model = Unit
        # We exclude auto-generated fields like unit_number
        fields = ['property', 'block', 'floor', 'door_number', 'is_locked', 'owner']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'block': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Block A'}),
            'floor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1'}),
            'door_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 05'}),
            'owner': forms.Select(attrs={'class': 'form-select'}), # Optional: Assign Landlord immediately
            'is_locked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BulkParkingCreationForm(forms.Form):
    property = forms.ModelChoiceField(
        queryset=Property.objects.none(),
        label="Select Property",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prefix = forms.CharField(
        initial="P", 
        label="Lot Prefix",
        help_text="e.g. 'P' generates P-1, P-2...",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    start_number = forms.IntegerField(
        initial=1, 
        min_value=1,
        label="Start Number",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    end_number = forms.IntegerField(
        initial=20, 
        min_value=1,
        label="End Number",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org', None)
        super().__init__(*args, **kwargs)
        if org:
            self.fields['property'].queryset = Property.objects.filter(organization=org)