from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, ManagerSignUpForm
from property.models import SoftwareInvoice # Needed to create the 20k invoice
from django.utils import timezone

def splash_page_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'splash_page.html')

# --- REGISTRATION VIEW (Updated for SaaS) ---
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = ManagerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 1. Create the initial "Integration Fee" invoice
            SoftwareInvoice.objects.create(
                organization=user.organization,
                amount=20000.00,
                description="One-Time System Integration Fee",
                due_date=timezone.now().date()
            )
            
            login(request, user)
            # 2. Redirect to Activation Pending instead of Home
            return redirect('users:activation_pending')
        else:
            messages.error(request, "Registration failed. Please check the information.")
    else:
        form = ManagerSignUpForm()

    return render(request, 'register.html', {'form': form})

# --- NEW: ACTIVATION PENDING VIEW ---
@login_required
def activation_pending_view(request):
    """
    Landing page for inactive organizations (haven't paid 20k).
    """
    org = request.user.organization
    if org and org.is_active:
        return redirect('home')
        
    return render(request, 'activation_pending.html', {'org': org})

# ... (Keep existing login_view and logout_view) ...
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
    messages.info(request, 'You have been successfully logged out.')
    return redirect('users:splash_page')