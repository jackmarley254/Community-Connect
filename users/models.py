from django.contrib.auth.models import AbstractUser
from django.db import models

class Organization(models.Model):
    """
    Represents a Property Management Company (e.g., Luxia Management).
    Moved here to prevent circular dependencies.
    """
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    """
    Unified User Model.
    Includes Role and Organization directly to avoid complex joins.
    """
    ROLE_CHOICES = [
        ('PM', 'Property Manager'),
        ('HO', 'Home Owner/Landlord'),
        ('T', 'Tenant'),
        ('SEC', 'Security Desk'),
    ]
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='T')
    
    # Link directly to the local Organization model
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='members'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"