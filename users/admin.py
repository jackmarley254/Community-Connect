from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

class UserProfileInline(admin.StackedInline):
    """
    Allows editing the UserProfile (Role/Organization) directly inside the User edit page.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class CustomUserAdmin(UserAdmin):
    """
    Custom Admin for the CustomUser model.
    """
    inlines = (UserProfileInline, )
    # Add phone_number to the list display and fieldsets if needed
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    
    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
        except:
            return "-"
    get_role.short_description = 'Role'

# Register the models
admin.site.register(CustomUser, CustomUserAdmin)
# You can also register UserProfile separately if you prefer
admin.site.register(UserProfile)