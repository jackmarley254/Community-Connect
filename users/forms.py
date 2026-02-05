from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser, Organization, SupportMessage

class LoginForm(AuthenticationForm):
    """
    Standard Django authentication form with Bootstrap classes applied.
    """
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))

class ManagerSignUpForm(UserCreationForm):
    """Sign up form for new SaaS Tenants (Property Managers)"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    company_name = forms.CharField(required=True, help_text="Name of your Property Management Company")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'company_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'PM'  # Force role to Property Manager
        
        if commit:
            company_name = self.cleaned_data['company_name']
            # Create the Organization automatically
            org = Organization.objects.create(name=company_name)
            user.organization = org
            user.save()
            
        return user

class CreateUserForm(UserCreationForm):
    """Form for PMs to add Landlords/Tenants/Staff manually"""
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'role')
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SupportMessageForm(forms.ModelForm):
    """Form for sending messages to Super Admin"""
    class Meta:
        model = SupportMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your message to Support...'})
        }