from django.contrib import admin
from .models import Property, Unit, Invoice, Ticket, Notification, ParkingLot, Announcement

# NOTE: Do NOT register Organization here. It is now registered in users/admin.py

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'total_units_count', 'occupancy_percentage')
    search_fields = ('name', 'organization__name')
    list_filter = ('organization',)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'property', 'owner', 'current_tenant')
    list_filter = ('property',)
    search_fields = ('unit_number', 'property__name', 'current_tenant__username')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'unit', 'amount', 'due_date', 'is_paid', 'sender_role')
    list_filter = ('is_paid', 'due_date', 'sender_role')
    search_fields = ('unit__unit_number',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'priority', 'status', 'submitted_by', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'unit__unit_number')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'posted_by', 'created_at')

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('lot_number', 'property', 'current_tenant')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'is_read', 'timestamp')