from django.shortcuts import redirect, render
from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

def role_required(allowed_roles):
    """
    Decorator to check if the user has one of the allowed roles.
    allowed_roles: list of strings, e.g., ['PM', 'HO']
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Redirect to login if not authenticated
                from django.conf import settings
                return redirect(settings.LOGIN_URL)
            
            # Allow superusers (Django's is_superuser) to access any 'ADMIN' area
            if 'ADMIN' in allowed_roles and request.user.is_superuser:
                 return view_func(request, *args, **kwargs)
            
            has_permission = False
            try:
                if request.user.userprofile.role in allowed_roles:
                    has_permission = True
            except:
                 return redirect('home')
            
            if has_permission:
                return view_func(request, *args, **kwargs)
            else:
                return render(request, 'base.html', {'error': 'Access Denied: You do not have permission to view this page.'})
                 
        return wrapper
    return decorator  