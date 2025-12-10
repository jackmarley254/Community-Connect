from django.contrib import admin
from .models import Organization, Property, Unit, ParkingLot, Notification, Ticket, Announcement, Invoice

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'address')
    list_filter = ('organization',)
    search_fields = ('name', 'address')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'property', 'owner', 'current_tenant')
    list_filter = ('property', 'property__organization')
    search_fields = ('unit_number', 'owner__username')
    autocomplete_fields = ['owner', 'current_tenant', 'property']

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('lot_number', 'property', 'owner', 'current_tenant')
    list_filter = ('property',)
    autocomplete_fields = ['owner', 'current_tenant', 'property']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'unit', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'unit__property')
    search_fields = ('title', 'unit__unit_number', 'description')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'posted_by', 'created_at', 'is_active')
    list_filter = ('property', 'is_active')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('unit', 'amount', 'due_date', 'is_paid')
    list_filter = ('is_paid', 'due_date', 'unit__property')