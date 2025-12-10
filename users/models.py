from django.contrib.auth.models import AbstractUser
from django.db import models

# NOTE: Do NOT import property here. We use a string reference below.

class CustomUser(AbstractUser):
    """
    Custom User Model extending Django's built-in User.
    """
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    """
    Holds role-specific data and links the user to their organization.
    """
    ROLE_CHOICES = (
        ('PM', 'Property Manager'),
        ('HO', 'Home Owner/Landlord'),
        ('T', 'Tenant'),
        ('SD', 'Security Desk'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='userprofile')
    
    # User's primary role
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default='T')
    
    # FIX IS HERE: We use the string 'property.Organization' (WITH QUOTES)
    organization = models.ForeignKey('property.Organization', on_delete=models.SET_NULL, null=True, blank=True,
                                     help_text="The organization this user belongs to.")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name_plural = "User Profiles"