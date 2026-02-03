from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser, Organization

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
    """
    SaaS Registration Form.
    Creates a User (PM) AND an Organization simultaneously.
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    company_name = forms.CharField(required=True, help_text="Name of your Property Management Company")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'company_name')

    def save(self, commit=True):
        # 1. Save the User first (but don't commit to DB yet if possible, though UserCreationForm usually does)
        user = super().save(commit=False)
        user.role = 'PM'  # Force role to Property Manager
        
        if commit:
            # 2. Create the Organization
            company_name = self.cleaned_data['company_name']
            org = Organization.objects.create(name=company_name)
            
            # 3. Link User to Organization
            user.organization = org
            user.save()
            
        return user