from django import forms
from .models import ShortTermStay, Unit

class CheckInForm(forms.ModelForm):
    # Helper field to find the unit by name (e.g., "A-104")
    unit_number = forms.CharField(
        max_length=20, 
        label="Unit Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A-104'})
    )
    
    class Meta:
        model = ShortTermStay
        fields = ['guest_name', 'guest_id_number', 'guest_phone', 'id_passport_image']
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guest Name'}),
            'guest_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID/Passport No.'}),
            'guest_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XX...'}),
            'id_passport_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_unit_number(self):
        # Validate that the unit exists before checking in
        unit_num = self.cleaned_data.get('unit_number')
        unit = Unit.objects.filter(unit_number__iexact=unit_num).first()
        if not unit:
            raise forms.ValidationError(f"Unit '{unit_num}' does not exist.")
        return unit

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = ShortTermStay
        fields = ['feedback_rating', 'feedback_comment']
        widgets = {
            'feedback_rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-select'}),
            'feedback_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comments...'}),
        }