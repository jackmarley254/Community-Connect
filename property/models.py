from django.db import models
from django.conf import settings
from users.models import Organization

# --- 1. Property Structure ---

class Property(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    blocks = models.CharField(max_length=255, help_text="Comma-separated blocks, e.g., 'Tower A, Tower B'", blank=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    @property
    def total_units_count(self): return self.unit_set.count()
    @property
    def occupied_units_count(self): return self.unit_set.filter(current_tenant__isnull=False).count()
    class Meta: verbose_name_plural = "Properties"

# --- NEW: Staff Assignment Model ---
class PropertyStaff(models.Model):
    """
    Links a Staff User (Guard/Caretaker) to a specific Property.
    This replaces the circular Foreign Key in CustomUser.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_assignment')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='staff_members')
    
    def __str__(self):
        return f"{self.user.username} -> {self.property.name}"

class Unit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    block = models.CharField(max_length=50, blank=True)
    floor = models.CharField(max_length=10)
    door_number = models.CharField(max_length=10)
    unit_number = models.CharField(max_length=20, editable=False)
    is_locked = models.BooleanField(default=False)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_units')
    organization_owner = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    current_tenant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='occupied_unit')

    def save(self, *args, **kwargs):
        prefix = f"{self.block}-" if self.block else ""
        self.unit_number = f"{prefix}{self.floor}{self.door_number}"
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.property.name} - {self.unit_number}"
    class Meta: unique_together = ('property', 'block', 'floor', 'door_number')

# --- 2. Visitor & Short Term ---
class VisitorLog(models.Model):
    VISITOR_TYPES = [('DELIVERY', 'Delivery'), ('SERVICE', 'Service'), ('SOCIAL', 'Social Visit'), ('TAXI', 'Taxi')]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='visitors')
    visitor_name = models.CharField(max_length=100)
    visitor_id_number = models.CharField(max_length=50, blank=True, null=True)
    visitor_phone = models.CharField(max_length=20, blank=True, null=True)
    id_collected_at_gate = models.BooleanField(default=False)
    visitor_type = models.CharField(max_length=20, choices=VISITOR_TYPES, default='SOCIAL')
    notified_tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    allowed_entry = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)

class ShortTermStay(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='short_term_stays')
    guest_name = models.CharField(max_length=255)
    guest_id_number = models.CharField(max_length=50)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    id_passport_image = models.ImageField(upload_to='guest_ids/%Y/%m/', blank=True, null=True)
    check_in_time = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stays_checked_in')
    check_out_time = models.DateTimeField(null=True, blank=True)
    checked_out_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stays_checked_out')
    is_active = models.BooleanField(default=True)
    feedback_rating = models.IntegerField(null=True, blank=True)
    feedback_comment = models.TextField(blank=True, null=True)

# --- 3. Financials & Others ---
class Invoice(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    description = models.CharField(max_length=200)
    sender_role = models.CharField(max_length=20, default='ORGANIZATION')
    mpesa_code = models.CharField(max_length=50, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self): return f"Invoice #{self.id} - {self.unit.unit_number} - {self.amount}"

class Ticket(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, default='MEDIUM')
    status = models.CharField(max_length=20, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self): return f"#{self.id} - {self.title}"

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='received_notifications' # <--- FIXED: Added related_name
    )
    message = models.TextField()
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_notifications' # <--- FIXED: Added related_name
    )
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self): return f"Alert for {self.recipient.username}"

class Announcement(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self): return f"{self.title} - {self.property.name}"

class ParkingLot(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    lot_number = models.CharField(max_length=10)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'HO'})
    current_tenant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_parking_lot', limit_choices_to={'role': 'T'})
    
    def __str__(self): return f"{self.property.name} - Lot {self.lot_number}"
    
    class Meta:
        unique_together = ('property', 'lot_number')
        verbose_name = "Parking Lot"
        verbose_name_plural = "Parking Lots"