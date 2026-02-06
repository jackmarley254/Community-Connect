from django.contrib import admin
from .models import Property, Unit, Invoice, Ticket, Notification, ParkingLot, Announcement, PropertyStaff, ShortTermStay, VisitorLog

# --- Staff Assignment Admin ---
@admin.register(PropertyStaff)
class PropertyStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'get_role')
    search_fields = ('user__username', 'property__name')
    
    def get_role(self, obj):
        return obj.user.get_role_display()
    get_role.short_description = 'Staff Role'

# --- Existing Admins ---

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'total_units_count')
    search_fields = ('name', 'organization__name')
    list_filter = ('organization',)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'property', 'block', 'floor', 'owner', 'current_tenant')
    list_filter = ('property', 'is_locked')
    search_fields = ('unit_number', 'property__name', 'current_tenant__username')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'unit', 'amount', 'due_date', 'is_paid', 'sender_role')
    list_filter = ('is_paid', 'due_date', 'sender_role')
    search_fields = ('unit__unit_number',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority')

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('visitor_name', 'unit', 'visitor_type', 'entry_time', 'is_active')
    list_filter = ('visitor_type', 'is_active')

@admin.register(ShortTermStay)
class ShortTermStayAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'unit', 'check_in_time', 'is_active')

# Register others simply
admin.site.register(Announcement)
admin.site.register(ParkingLot)
admin.site.register(Notification)