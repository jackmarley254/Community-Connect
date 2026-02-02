from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.utils import timezone
from users.decorators import role_required
from users.models import CustomUser
from .models import Property, Unit, ParkingLot, Notification, Ticket, Announcement, Invoice
from .mpesa import lipa_na_mpesa_online
from django.views.decorators.csrf import csrf_exempt
import json
# --- HELPER ---

def get_user_organization(user):
    """Safely retrieves the user's organization."""
    try:
        return user.userprofile.organization 
    except AttributeError:
        return None

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
@role_required(['SD'])
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
            
            # Find the default owner
            default_owner = None
            if owner_id:
                default_owner = CustomUser.objects.filter(id=owner_id, userprofile__role='HO').first()
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
            
    home_owners = CustomUser.objects.filter(userprofile__role='HO').order_by('username')
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
@role_required(['PM', 'ADMIN'])
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
@role_required(['SD']) 
@require_POST
def security_desk_notify_api(request):
    unit_number = request.POST.get('unit_number')
    message = request.POST.get('message')
    org = get_user_organization(request.user)

    if not unit_number or not message or not org:
        return JsonResponse({'status': 'error', 'message': 'Invalid data.'}, status=400)

    try:
        target_unit = Unit.objects.get(
            property__organization=org,
            unit_number__iexact=unit_number,
            current_tenant__isnull=False 
        )
        Notification.objects.create(
            recipient=target_unit.current_tenant,
            message=message,
            sender=request.user,
        )
        return JsonResponse({'status': 'success', 'message': 'Alert sent.'})
    except Unit.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': f'Unit {unit_number} not found.'}, status=404)


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
@role_required(['PM', 'ADMIN'])
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
        
        # 1. Get Tenant's Phone Number (Assuming it's stored in CustomUser)
        phone_number = request.user.phone_number 
        # Ensure phone format is 2547XXXXXXXX
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        # 2. Initiate STK Push
        response = lipa_na_mpesa_online(
            phone_number=phone_number,
            amount=invoice.amount,
            account_reference=f"INV-{invoice.id}",
            transaction_desc=f"Payment for Invoice #{invoice.id}"
        )
        
        if 'ResponseCode' in response and response['ResponseCode'] == '0':
            # STK Push sent successfully
            # NOTE: We do NOT mark as paid yet. We wait for the Callback.
            return JsonResponse({'status': 'success', 'message': 'STK Push sent to your phone. Please enter PIN to complete payment.'})
        else:
            error_msg = response.get('errorMessage', 'Failed to initiate payment.')
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)

    except Invoice.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invoice not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt # Daraja won't have your CSRF token
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')

            if result_code == 0:
                # Payment Successful!
                meta_data = stk_callback.get('CallbackMetadata', {}).get('Item', [])

                # Extract Receipt Number (M-Pesa Code)
                receipt_number = next((item['Value'] for item in meta_data if item['Name'] == 'MpesaReceiptNumber'), None)

                # You usually don't get the AccountReference back in the callback directly in Sandbox.
                # In production, you might map the CheckoutRequestID to your Invoice.
                # For simplicity here, you'd need to store the CheckoutRequestID when sending the request 
                # to link it back to the invoice later.

                print(f"Payment Confirmed: {receipt_number}")
                # logic to find invoice and mark as paid would go here

            else:
                print("Payment Failed or Cancelled")

        except Exception as e:
            print(f"Callback Error: {e}")

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@login_required
@role_required(['PM'])
def property_details_view(request, property_id):
    """
    Detailed view for a specific Property.
    Shows: Landlords list, Transaction History (Payments).
    """
    org = get_user_organization(request.user)
    if not org:
        messages.error(request, "No Organization found.")
        return redirect('property:pm_dashboard')

    # Fetch the property, ensuring it belongs to the PM's organization
    property_obj = get_object_or_404(Property, id=property_id, organization=org)
    
    # 1. Get all units in this property
    units = Unit.objects.filter(property=property_obj).select_related('owner')
    
    # 2. Get distinct Landlords (Home Owners)
    # We filter units that have an owner, then get distinct user IDs
    landlord_ids = units.values_list('owner_id', flat=True).distinct()
    landlords = CustomUser.objects.filter(id__in=landlord_ids)
    
    # 3. Get Payment Transactions (Paid Invoices)
    # This allows the PM to "pick payment details"
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