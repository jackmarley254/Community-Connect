from django import forms
from .models import ShortTermStay, Unit, MeterReading, Expense, PaymentConfiguration, ExpenseCategory

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