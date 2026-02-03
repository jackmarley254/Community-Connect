from functools import wraps
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    """
    Decorator to check if the user has one of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:auth_login')
            
            # Superuser Override
            if request.user.is_superuser:
                 return view_func(request, *args, **kwargs)
            
            # Check Role
            user_role = getattr(request.user, 'role', None)

            # DEBUG: Print to logs if you need to see what's happening
            # print(f"User: {request.user.username}, Role: {user_role}, Allowed: {allowed_roles}")

            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # STOP THE LOOP: Do NOT redirect to home. 
            # Show a clear error message instead.
            return HttpResponseForbidden(f"""
                <div style='text-align:center; padding-top:50px;'>
                    <h1>403 Access Denied</h1>
                    <p>User <b>{request.user.username}</b> (Role: {user_role}) is not authorized for this page.</p>
                    <p>Required Roles: {allowed_roles}</p>
                    <a href='/auth/logout/'>Logout</a>
                </div>
            """)
                 
        return wrapper
    return decorator