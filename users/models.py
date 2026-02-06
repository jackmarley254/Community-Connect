from django.contrib.auth.models import AbstractUser
from django.db import models

class Organization(models.Model):
    """
    Represents a Property Management Company (e.g., Luxia Management).
    """
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Organizations"

class CustomUser(AbstractUser):
    """
    Unified User Model.
    Includes Role, Organization, and specific Property Assignment for staff.
    """
    ROLE_CHOICES = [
        ('PM', 'Property Manager'),
        ('HO', 'Home Owner/Landlord'),
        ('T', 'Tenant'),
        ('SEC', 'Security Desk'),
        ('CT', 'Caretaker'), # NEW: Added Caretaker role
    ]
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='T')
    
    # Link directly to the Organization (SaaS Tenant)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='members',
        help_text="The organization this user belongs to."
    )
    
    # NEW: Link Staff (Guard/Caretaker) to a specific property
    # We use a string reference 'property.Property' to avoid circular imports

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class SupportMessage(models.Model):
    """
    Direct line of communication between Property Managers and SaaS Super Admin.
    """
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_support_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # If True, this is a reply from the SaaS Owner to the Client
    is_from_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Msg from {self.sender.username}: {self.message[:20]}..."