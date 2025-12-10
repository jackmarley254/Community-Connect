from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import LoginForm
from django.conf import settings

def splash_page_view(request):
    if request.user.is_authenticated:
        # If logged in, send them to their role-based home
        return redirect('home')
    return render(request, 'splash_page.html')

@login_required
def home_view(request):
    """Redirects authenticated users to their appropriate dashboard."""
    try:
        role = request.user.userprofile.role
        if role == 'PM':
            return redirect('property:pm_dashboard')
        elif role == 'HO':
            return redirect('property:ho_dashboard')
        elif role == 'T':
            return redirect('property:tenant_dashboard')
        elif role == 'SD':
            return redirect('property:security_desk')
    except Exception:
        pass
    
    return render(request, 'base.html', {'message': 'Welcome! Please contact admin to assign a role.'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('users:auth_login')