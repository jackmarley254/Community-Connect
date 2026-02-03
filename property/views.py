from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.utils import timezone
from users.decorators import role_required
from users.models import CustomUser, Organization
from .models import Property, Unit, ParkingLot, Notification, Ticket, Announcement, Invoice
# Check if mpesa file exists, otherwise mock it to prevent import error
try:
    from .mpesa import lipa_na_mpesa_online
except ImportError:
    def lipa_na_mpesa_online(**kwargs): return {'ResponseCode': '0', 'errorMessage': 'Simulated Payment'}

from django.views.decorators.csrf import csrf_exempt
import json
import datetime
from django.db.models import Count, Q

# --- HELPER ---

def get_user_organization(user):
    """
    Safely retrieves the user's organization.
    Updated to use CustomUser.organization directly.
    """
    # 1. Direct assignment (PM, Security)
    if user.organization:
        return user.organization
    
    # 2. Derive from ownership (Home Owner)
    if user.role == 'HO':
        unit = Unit.objects.filter(owner=user).select_related('property__organization').first()
        if unit:
            return unit.property.organization
            
    return None

# ==========================================
# 1. THE DISPATCHER (Traffic Cop)
# ==========================================
@login_required
def dashboard_redirect_view(request):
    """
    Redirects the user to their specific dashboard based on their Role.
    Linked to the '/home/' URL.
    """
    user = request.user
    
    if user.role == 'PM':
        return redirect('property:pm_dashboard')
    elif user.role == 'HO':
        return redirect('property:ho_dashboard')
    elif user.role == 'T':
        return redirect('property:tenant_dashboard')
    elif user.role == 'SEC':
        return redirect('property:security_desk')
    elif user.is_superuser:
        return redirect('admin:index')
    else:
        messages.warning(request, "Account has no role assigned.")
        return redirect('users:auth_login')

# --- DASHBOARD VIEWS ---

@login_required
@role_required(['PM'])
def pm_dashboard_view(request):
    """Property Manager: View all properties, unit stats, and financial breakdown."""
    org = get_user_organization(request.user)
    if not org:
        return render(request, 'base.html', {'error': 'No Organization found.'})
        
    properties = Property.objects.filter(organization=org).order_by('name')
    
    # Stats
    all_units = Unit.objects.filter(property__organization=org)
    total_units = all_units.count()
    occupied_units = all_units.filter(current_tenant__isnull=False).count()
    
    # Financial Breakdown for Units
    unit_financial_data = []
    
    for unit in all_units:
        latest_invoice = Invoice.objects.filter(unit=unit).order_by('-due_date').first()
        
        status = 'Vacant'
        amount_due = 0
        due_date = None
        
        if latest_invoice:
            amount_due = latest_invoice.amount
            due_date = latest_invoice.due_date
            if latest_invoice.is_paid:
                status = 'Paid'
            else:
                status = 'Outstanding'
        elif unit.current_tenant:
             status = 'No Invoice'
        
        unit_financial_data.append({
            'unit_number': unit.unit_number,
            'property_name': unit.property.name,
            'tenant': unit.current_tenant.username if unit.current_tenant else 'N/A',
            'amount_due': amount_due,
            'due_date': due_date,
            'status': status,
        })
    
    context = {
        'organization_name': org.name,
        'properties': properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'occupancy_rate': f"{occupied_units / total_units * 100:.1f}%" if total_units else "0.0%",
        'unit_financial_data': unit_financial_data,
    }
    return render(request, 'pm_dashboard.html', context)


@login_required
@role_required(['HO'])
def ho_dashboard_view(request):
    """Home Owner/Landlord: View owned units, tenants, parking, AND Invoices."""
    # Units owned by this user
    owned_units = Unit.objects.filter(owner=request.user).select_related('property', 'current_tenant')
    owned_parking = ParkingLot.objects.filter(owner=request.user).select_related('property', 'current_tenant')
    
    # Fetch Invoices linked to units owned by this user
    my_invoices = Invoice.objects.filter(unit__owner=request.user).order_by('-due_date')
    
    # Tenants available for assignment
    current_tenants_data = [{'id': unit.current_tenant.id, 'username': unit.current_tenant.username, 'unit_number': unit.unit_number} 
                        for unit in owned_units if unit.current_tenant]
    
    context = {
        'owned_units': owned_units,
        'owned_parking': owned_parking,
        'current_tenants_json': current_tenants_data,
        'invoices': my_invoices,
    }
    return render(request, 'ho_dashboard.html', context)


@login_required
@role_required(['T'])
def tenant_dashboard_view(request):
    """Updated Tenant Dashboard with Tickets, Announcements and Invoices."""
    try:
        unit = Unit.objects.get(current_tenant=request.user)
        # Fetch Announcements
        announcements = Announcement.objects.filter(property=unit.property, is_active=True).order_by('-created_at')
        # Fetch My Tickets
        my_tickets = Ticket.objects.filter(unit=unit).order_by('-created_at')
        # Fetch My Invoices (Rent/Service Charge)
        my_invoices = Invoice.objects.filter(unit=unit).order_by('-due_date')
    except Unit.DoesNotExist:
        unit = None
        announcements = []
        my_tickets = []
        my_invoices = []
    
    try:
        parking = ParkingLot.objects.get(current_tenant=request.user)
    except ParkingLot.DoesNotExist:
        parking = None
        
    historical_notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')[:5]
    
    context = {
        'unit': unit,
        'parking': parking,
        'historical_notifications': historical_notifications,
        'announcements': announcements,
        'my_tickets': my_tickets,
        'my_invoices': my_invoices,
    }
    return render(request, 'tenant_dashboard.html', context)


@login_required
@role_required(['SEC'])
def security_desk_view(request):
    org = get_user_organization(request.user)
    context = {'organization_name': org.name if org else 'Unassigned Organization'}
    return render(request, 'security_desk.html', context)


# --- FEATURE VIEWS ---

@login_required
@role_required(['PM'])
def bulk_create_units_view(request):
    org = get_user_organization(request.user)
    if not org:
        messages.error(request, "User is not linked to an organization.")
        return redirect('property:pm_dashboard')

    properties = Property.objects.filter(organization=org).order_by('name')
    
    if request.method == 'POST':
        property_id = request.POST.get('property_id')
        start_num_str = request.POST.get('start_num')
        end_num_str = request.POST.get('end_num')
        owner_id = request.POST.get('default_owner_id')
        
        try:
            target_property = Property.objects.get(id=property_id, organization=org)
            start_num = int(start_num_str)
            end_num = int(end_num_str)
            
            # Find the default owner (Updated to check role directly)
            default_owner = None
            if owner_id:
                default_owner = CustomUser.objects.filter(id=owner_id, role='HO').first()
                if not default_owner:
                    messages.error(request, "Invalid default owner selected.")
                    return render(request, 'bulk_create_units.html', {'properties': properties})

            if start_num > end_num:
                messages.error(request, "Start number must be less than end number.")
                return render(request, 'bulk_create_units.html', {'properties': properties})

            new_units = []
            
            for i in range(start_num, end_num + 1):
                unit_number = str(i)
                if not Unit.objects.filter(property=target_property, unit_number=unit_number).exists():
                    new_units.append(
                        Unit(
                            property=target_property,
                            unit_number=unit_number,
                            owner=default_owner
                        )
                    )
            
            with transaction.atomic():
                Unit.objects.bulk_create(new_units)

            messages.success(request, f"Successfully created {len(new_units)} new units.")
            return redirect('property:pm_dashboard')

        except Exception as e:
            messages.error(request, f"Error: {e}")
            
    # Updated filter to use 'role' instead of 'userprofile__role'
    home_owners = CustomUser.objects.filter(role='HO').order_by('username')
    context = {
        'properties': properties,
        'home_owners': home_owners
    }
    return render(request, 'bulk_create_units.html', context)


@login_required
@role_required(['T'])
def create_ticket_view(request):
    """Allow tenants to raise a maintenance ticket."""
    try:
        tenant_unit = Unit.objects.get(current_tenant=request.user)
    except Unit.DoesNotExist:
        return render(request, 'base.html', {'error': 'No unit assigned to you.'})

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        
        Ticket.objects.create(
            unit=tenant_unit,
            submitted_by=request.user,
            title=title,
            description=description,
            priority=priority
        )
        return redirect('property:tenant_dashboard')
    
    return render(request, 'ticket_create.html')


@login_required
@role_required(['PM'])
def invoice_admin_view(request):
    org = get_user_organization(request.user)
    if not org:
        messages.error(request, "No Organization found.")
        return redirect('property:pm_dashboard')

    invoices = Invoice.objects.filter(unit__property__organization=org).order_by('-due_date', 'is_paid')
    return render(request, 'invoice_admin.html', {'invoices': invoices})


@login_required
@role_required(['HO'])
def ho_create_rent_invoice_view(request):
    owned_units = Unit.objects.filter(owner=request.user, current_tenant__isnull=False).select_related('current_tenant')
    
    if request.method == 'POST':
        unit_id = request.POST.get('unit_id')
        amount = request.POST.get('amount')
        due_date_str = request.POST.get('due_date')
        description = request.POST.get('description')
        
        try:
            target_unit = Unit.objects.get(id=unit_id, owner=request.user)
            
            Invoice.objects.create(
                unit=target_unit,
                amount=amount,
                due_date=due_date_str,
                description=description or f"Rent for {target_unit.unit_number}",
                sender_role='LANDLORD',
                is_paid=False
            )
            messages.success(request, f"Rent invoice sent to tenant in Unit {target_unit.unit_number}.")
            return redirect('property:ho_dashboard')
            
        except Unit.DoesNotExist:
            messages.error(request, "Invalid unit selected.")
        except Exception as e:
            messages.error(request, f"Error creating invoice: {e}")

    return render(request, 'ho_create_rent_invoice.html', {'units_with_tenants': owned_units})


# --- API ENDPOINTS ---

@login_required
@require_POST
def security_desk_notify_api(request):
    try:
        data = json.loads(request.body)
        unit_number = data.get('unit_num') # Matched frontend JS key 'unit_num'
        message = data.get('message')
        org = get_user_organization(request.user)

        if not unit_number or not message or not org:
            return JsonResponse({'status': 'error', 'message': 'Invalid data or no org.'}, status=400)

        # Simplified unit finding logic
        target_unit = Unit.objects.filter(
            property__organization=org,
            unit_number=unit_number,
            current_tenant__isnull=False 
        ).first()
        
        if target_unit:
            Notification.objects.create(
                recipient=target_unit.current_tenant,
                message=message,
                sender=request.user,
            )
            return JsonResponse({'status': 'success', 'message': 'Alert sent.'})
        else:
            return JsonResponse({'status': 'error', 'message': f'Unit {unit_number} not found or vacant.'}, status=404)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@role_required(['T'])
@require_GET
def get_unread_notifications_api(request):
    tenant_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).order_by('-timestamp')

    data = [{'id': n.id, 'message': n.message, 'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for n in tenant_notifications]

    if tenant_notifications.exists():
        tenant_notifications.update(is_read=True)
    
    return JsonResponse({'notifications': data, 'count': len(data)})


@login_required
@role_required(['HO'])
@require_POST
def ho_assign_parking_api(request):
    try:
        lot_id = request.POST.get('lot_id')
        tenant_id = request.POST.get('tenant_id') 
        
        parking_lot = ParkingLot.objects.get(id=lot_id, owner=request.user)
        tenant_user = CustomUser.objects.get(id=tenant_id)
        
        # Verify tenant belongs to HO
        if not Unit.objects.filter(owner=request.user, current_tenant=tenant_user).exists():
            return JsonResponse({'status': 'error', 'message': 'Invalid tenant selection.'}, status=403)

        # Remove old assignment if exists
        existing = ParkingLot.objects.filter(current_tenant=tenant_user).exclude(id=lot_id).first()
        if existing:
            existing.current_tenant = None
            existing.save()

        parking_lot.current_tenant = tenant_user
        parking_lot.save()

        return JsonResponse({'status': 'success', 'message': 'Parking assigned.'})

    except (ParkingLot.DoesNotExist, CustomUser.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Not found.'}, status=404)


@login_required
@role_required(['PM'])
@require_POST
def mark_invoice_paid_api(request):
    invoice_id = request.POST.get('invoice_id')
    org = get_user_organization(request.user)
    
    try:
        invoice = Invoice.objects.get(
            id=invoice_id,
            unit__property__organization=org
        )
        invoice.is_paid = True
        invoice.payment_date = timezone.now()
        invoice.save()
        
        return JsonResponse({'status': 'success', 'message': f'Invoice #{invoice_id} marked as paid.'})
    except Invoice.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invoice not found or unauthorized.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@role_required(['T'])
@require_POST
def tenant_pay_invoice_api(request):
    invoice_id = request.POST.get('invoice_id')
    
    try:
        invoice = Invoice.objects.get(id=invoice_id, unit__current_tenant=request.user, is_paid=False)
        
        # 1. Get Tenant's Phone Number
        phone_number = request.user.phone_number 
        if phone_number and phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        if not phone_number:
             return JsonResponse({'status': 'error', 'message': 'Please update your phone number in profile.'}, status=400)

        # 2. Initiate STK Push
        response = lipa_na_mpesa_online(
            phone_number=phone_number,
            amount=invoice.amount,
            account_reference=f"INV-{invoice.id}",
            transaction_desc=f"Payment for Invoice #{invoice.id}"
        )
        
        if 'ResponseCode' in response and response['ResponseCode'] == '0':
            return JsonResponse({'status': 'success', 'message': 'STK Push sent to your phone.'})
        else:
            error_msg = response.get('errorMessage', 'Failed to initiate payment.')
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)

    except Invoice.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invoice not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def mpesa_callback(request):
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@login_required
@role_required(['PM'])
def property_details_view(request, property_id):
    """
    Detailed view for a specific Property.
    """
    org = get_user_organization(request.user)
    if not org:
        messages.error(request, "No Organization found.")
        return redirect('property:pm_dashboard')

    property_obj = get_object_or_404(Property, id=property_id, organization=org)
    
    units = Unit.objects.filter(property=property_obj).select_related('owner')
    landlord_ids = units.values_list('owner_id', flat=True).distinct()
    landlords = CustomUser.objects.filter(id__in=landlord_ids)
    
    transactions = Invoice.objects.filter(
        unit__property=property_obj, 
        is_paid=True
    ).select_related('unit', 'unit__current_tenant').order_by('-payment_date')

    context = {
        'property': property_obj,
        'landlords': landlords,
        'transactions': transactions,
        'total_units': units.count(),
        'occupied_units': units.filter(current_tenant__isnull=False).count(),
    }
    return render(request, 'property_details.html', context)

# --- ADDED THIS TO FIX URL ERROR ---
@login_required
@role_required(['PM'])
def unit_details_view(request, unit_id):
    """
    Detailed view for a specific Unit.
    """
    unit = get_object_or_404(Unit, id=unit_id)
    return render(request, 'unit_details.html', {'unit': unit})

# --- DEMO DATA SEEDER ---
def seed_data_view(request):
    if CustomUser.objects.filter(username='manager').exists():
        return HttpResponse("<h3>⚠️ Setup already done!</h3><p>Users already exist.</p><a href='/auth/login/'>Go to Login</a>")

    try:
        org = Organization.objects.create(
            name="Luxia Management", 
            address="Nairobi, CBD", 
            contact_email="info@luxia.com"
        )
        
        # NOTE: Updated to pass role/org directly to create_user
        CustomUser.objects.create_user(username="manager", email="pm@luxia.com", password="pass123", role='PM', organization=org)
        ho = CustomUser.objects.create_user(username="owner", email="landlord@gmail.com", password="pass123", role='HO')
        tenant = CustomUser.objects.create_user(username="tenant", email="tenant@gmail.com", password="pass123", role='T')
        CustomUser.objects.create_user(username="guard", email="security@luxia.com", password="pass123", role='SEC', organization=org)
        CustomUser.objects.create_superuser(username="admin", email="admin@luxia.com", password="pass123")

        prop = Property.objects.create(name="Sunset Apartments", address="Westlands, Nairobi", organization=org)
        unit = Unit.objects.create(property=prop, unit_number="101", owner=ho, current_tenant=tenant)

        Invoice.objects.create(
            unit=unit,
            amount=15000.00,
            due_date=datetime.date.today(),
            description="February Rent",
            is_paid=False,
            sender_role='ORGANIZATION'
        )

        return HttpResponse("""
            <h1 style='color:green'>✅ System Setup Complete!</h1>
            <ul>
                <li><b>Manager:</b> manager / pass123</li>
                <li><b>Owner:</b> owner / pass123</li>
                <li><b>Tenant:</b> tenant / pass123</li>
                <li><b>Security:</b> guard / pass123</li>
            </ul>
            <a href='/auth/login/'>Click here to Login</a>
        """)

    except Exception as e:
        return HttpResponse(f"<h1 style='color:red'>❌ Error</h1><p>{str(e)}</p>")