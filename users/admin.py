from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Organization

# We no longer need UserProfileInline because the fields are now directly on the User model.

class CustomUserAdmin(UserAdmin):
    """
    Custom Admin for the CustomUser model.
    """
    model = CustomUser
    
    # 1. Columns to show in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'organization', 'is_staff')
    
    # 2. Filters on the right sidebar
    list_filter = ('role', 'organization', 'is_staff', 'is_active')
    
    # 3. Fields to show when EDITING a user
    # We append our custom fields to the default Django User fields
    fieldsets = UserAdmin.fieldsets + (
        ('Luxia Connect Info', {'fields': ('role', 'organization', 'phone_number')}),
    )
    
    # 4. Fields to show when CREATING a user
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Luxia Connect Info', {'fields': ('role', 'organization', 'phone_number')}),
    )

    search_fields = ('username', 'email', 'organization__name')
    ordering = ('username',)

# Register the models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Organization)