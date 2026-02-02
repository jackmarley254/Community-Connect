from django.db import models
from django.conf import settings

# --- 1. Multi-Tenancy / Organization ---

class Organization(models.Model):
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Organizations"


# --- 2. Property Structure ---

class Property(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    # --- HELPER METHODS FOR DASHBOARD ---
    @property
    def total_units_count(self):
        return self.unit_set.count()

    @property
    def occupied_units_count(self):
        return self.unit_set.filter(current_tenant__isnull=False).count()

    @property
    def occupancy_percentage(self):
        total = self.total_units_count
        if total == 0:
            return 0
        occupied = self.occupied_units_count
        return int((occupied / total) * 100)

    class Meta:
        verbose_name_plural = "Properties"

class Unit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=10)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              limit_choices_to={'userprofile__role': 'HO'}, 
                              related_name='owned_units')
    
    # NEW: Allow the owning organization to be tracked for company-owned units
    organization_owner = models.ForeignKey('property.Organization', on_delete=models.SET_NULL, null=True, blank=True,
                                            help_text="Used if the unit is owned directly by the management company/organization.")
    
    current_tenant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                          limit_choices_to={'userprofile__role': 'T'}, 
                                          related_name='occupied_unit')

    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"
    
    class Meta:
        unique_together = ('property', 'unit_number')

class Invoice(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    description = models.CharField(max_length=200, default="Service Charge / Rent")
    
    # NEW: Track who created the invoice (Organization=Service Charge, HO=Rent/Other Fees)
    sender_role = models.CharField(max_length=20, choices=[('ORGANIZATION', 'Organization'), ('LANDLORD', 'Landlord')], default='ORGANIZATION')
    
    # NEW: MPESA Tracking Fields
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.unit.unit_number} - {self.amount}"

class ParkingLot(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    lot_number = models.CharField(max_length=10)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                              limit_choices_to={'userprofile__role': 'HO'}, 
                              related_name='owned_parking_lots')
    
    current_tenant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                          limit_choices_to={'userprofile__role': 'T'}, 
                                          related_name='assigned_parking_lot')
    
    def __str__(self):
        return f"{self.property.name} - Lot {self.lot_number}"
    
    class Meta:
        unique_together = ('property', 'lot_number')
        verbose_name = "Parking Lot"
        verbose_name_plural = "Parking Lots"


# --- 3. Notification System ---

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                  limit_choices_to={'userprofile__role': 'T'},
                                  related_name='tenant_notifications')
    
    message = models.TextField(max_length=500)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='sent_notifications')
    
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Alert for {self.recipient.username}"


# --- 4. Complaint & Ticketing System (Pillar II) ---

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    )
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('EMERGENCY', 'Emergency'),
    )

    # Link to the specific unit raising the issue
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tickets')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: For tracking who is fixing it (e.g., "Technician Assigned")
    assigned_to = models.CharField(max_length=100, blank=True, null=True, help_text="Name of technician or staff assigned.")

    def __str__(self):
        return f"#{self.id} - {self.title} ({self.get_status_display()})"


# --- 5. Digital Notice Board (Pillar II) ---

class Announcement(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.property.name}"


# --- 6. Financial Management (Pillar I - Basic Structure) ---

class Invoice(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    description = models.CharField(max_length=200, default="Monthly Service Charge")
    payment_date = models.DateTimeField(null=True, blank=True)
    mpesa_code = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.unit.unit_number} - {self.amount}"