from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:auth_login')
            
            # --- SAAS CHECK ---
            # If user belongs to an org, check if it is active
            if request.user.organization and not request.user.organization.is_active:
                # Allow them to see the activation page, but block dashboards
                if request.resolver_match.url_name != 'activation_pending':
                    return redirect('users:activation_pending')
            # ------------------

            if request.user.is_superuser:
                 return view_func(request, *args, **kwargs)
            
            user_role = getattr(request.user, 'role', None)
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("<h1>403 Access Denied</h1>")     
        return wrapper
    return decorator