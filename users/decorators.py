from functools import wraps
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib import messages

def role_required(allowed_roles):
    """
    Decorator to check if the user has one of the allowed roles.
    Updated to use CustomUser.role directly (Removed UserProfile dependency).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 1. Check if user is logged in
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            
            # 2. Allow Superusers if 'ADMIN' is in the allowed list
            if 'ADMIN' in allowed_roles and request.user.is_superuser:
                 return view_func(request, *args, **kwargs)
            
            # 3. Check Role (DIRECTLY on the user object now)
            # We use getattr to be safe, defaulting to None if something is wrong
            user_role = getattr(request.user, 'role', None)

            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # 4. Access Denied Logic
            # It's often better to redirect to home with an error message 
            # than to render a broken page.
            messages.error(request, "Access Denied: You do not have permission to view this page.")
            return redirect('home')
                 
        return wrapper
    return decorator