from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, ManagerSignUpForm

def splash_page_view(request):
    """
    Landing page. If already logged in, go straight to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'splash_page.html')

# --- NEW: REGISTRATION VIEW ---
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = ManagerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Auto-login after signup
            messages.success(request, f"Welcome to Luxia Connect! Organization '{user.organization.name}' created.")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please check the information.")
    else:
        form = ManagerSignUpForm()

    return render(request, 'register.html', {'form': form})

def login_view(request):
    """
    Handles user login.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect to the 'home' URL, which uses our Property Traffic Cop
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('users:splash_page')

# NOTE: We removed 'home_view' from here because we are using 
# 'property.views.dashboard_redirect_view' as the main dispatcher now.