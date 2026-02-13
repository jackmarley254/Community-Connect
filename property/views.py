from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.db.models import Sum, Count, Q
import json
import datetime
from .models import PaymentConfiguration, Invoice
from .mpesa import lipa_na_mpesa_online 

# --- CUSTOM IMPORTS ---
from users.decorators import role_required
from users.models import CustomUser, Organization, SupportMessage
from users.forms import CreateUserForm, SupportMessageForm
from .models import Property, Unit, ParkingLot, Notification, Ticket, Announcement, Invoice, ShortTermStay, VisitorLog, PaymentConfiguration, Meter, MeterReading, Expense, ExpenseCategory
from .forms import CheckInForm, FeedbackForm, MeterReadingForm, ExpenseForm, PaymentConfigForm

@login_required
@role_required(['PM'])
def pm_settings_view(request):
    org = get_user_organization(request.user)
    
    # Get or create the config object
    config, created = PaymentConfiguration.objects.get_or_create(organization=org)
    
    if request.method == 'POST':
        # Simple manual form handling for now
        config.paybill_number = request.POST.get('paybill')
        config.business_shortcode = request.POST.get('shortcode')
        config.consumer_key = request.POST.get('key')
        config.consumer_secret = request.POST.get('secret')
        config.passkey = request.POST.get('passkey')
        
        # Mark as configured if fields are filled
        if config.paybill_number and config.consumer_key:
            config.is_configured = True
            
        config.save()
        messages.success(request, "Payment settings updated successfully.")
        return redirect('property:pm_dashboard')
        
    return render(request, 'pm_settings.html', {'config': config})

# Check if mpesa file exists, otherwise mock it
try:
    from .mpesa import lipa_na_mpesa_online
except ImportError:
    def lipa_na_mpesa_online(**kwargs): return {'ResponseCode': '0', 'errorMessage': 'Simulated Payment'}

from django.views.decorators.csrf import csrf_exempt

# --- HELPER ---
def get_user_organization(user):
    """Safely retrieves the user's organization."""
    if user.organization:
        return user.organization
    # Derive from ownership (Home Owner)
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
    user = request.user
    if user.is_superuser:
        return redirect('property:super_admin_dashboard')
    elif user.role == 'PM':
        return redirect('property:pm_dashboard')
    elif user.role == 'HO':
        return redirect('property:ho_dashboard')
    elif user.role == 'T':
        return redirect('property:tenant_dashboard')
    elif user.role == 'SEC':
        return redirect('property:security_desk')
    else:
        messages.warning(request, "Account has no role assigned.")
        return redirect('users:auth_login')

# ==========================================
# 2. SUPER ADMIN (SAAS OWNER)
# ==========================================
@login_required
def super_admin_dashboard_view(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    # Global Stats
    total_orgs = Organization.objects.count()
    total_landlords = CustomUser.objects.filter(role='HO').count()
    total_revenue = Invoice.objects.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    active_properties = Property.objects.count()
    
    messages_list = SupportMessage.objects.select_related('sender__organization').order_by('-created_at')[:20]
    organizations = Organization.objects.annotate(user_count=Count('members')).order_by('-created_at')

    context = {
        'total_orgs': total_orgs,
        'total_landlords': total_landlords,
        'total_revenue': total_revenue,
        'active_properties': active_properties,
        'messages': messages_list,
        'organizations': organizations
    }
    return render(request, 'super_admin_dashboard.html', context)

# ==========================================
# 3. PM HQ DASHBOARD (Aggregated)
# ==========================================
@login_required
@role_required(['PM'])
def pm_dashboard_view(request):
    org = get_user_organization(request.user)
    if not org:
        return render(request, 'base.html', {'error': 'No Organization found.'})
        
    # 1. Scope: All properties in this Org
    properties = Property.objects.filter(organization=org).annotate(
        total_units=Count('unit'),
        occupied_units=Count('unit', filter=Q(unit__current_tenant__isnull=False))
    ).order_by('name')
    
    # 2. Financial Aggregation (Global)
    all_org_invoices = Invoice.objects.filter(unit__property__organization=org)
    total_revenue = all_org_invoices.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_arrears = all_org_invoices.filter(is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 3. Operational Stats
    total_properties = properties.count()
    total_units_portfolio = properties.aggregate(Sum('total_units'))['total_units__sum'] or 0
    total_occupied_portfolio = properties.aggregate(Sum('occupied_units'))['occupied_units__sum'] or 0
    
    portfolio_occupancy = 0
    if total_units_portfolio > 0:
        portfolio_occupancy = int((total_occupied_portfolio / total_units_portfolio) * 100)

    # Support Form
    support_form = SupportMessageForm()
    if request.method == 'POST' and 'support_msg' in request.POST:
        s_form = SupportMessageForm(request.POST)
        if s_form.is_valid():
            msg = s_form.save(commit=False)
            msg.sender = request.user
            msg.save()
            messages.success(request, "Message sent to Super Admin.")
            return redirect('property:pm_dashboard')

    context = {
        'org': org,
        'properties': properties,
        'total_revenue': total_revenue,
        'total_arrears': total_arrears,
        'portfolio_occupancy': portfolio_occupancy,
        'total_properties': total_properties,
        'support_form': support_form
    }
    return render(request, 'pm_dashboard.html', context)

# --- PM ACTIONS ---
@login_required
@role_required(['PM'])
def pm_create_user_view(request):
    org = get_user_organization(request.user)
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.organization = org
            user.save()
            messages.success(request, f"User {user.username} created.")
            return redirect('property:pm_dashboard')
    else:
        form = CreateUserForm()
    return render(request, 'pm_create_user.html', {'form': form})

@login_required
@role_required(['PM'])
def pm_create_announcement_view(request):
    org = get_user_organization(request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        property_id = request.POST.get('property_id')
        
        if property_id == 'all':
            props = Property.objects.filter(organization=org)
            for p in props:
                Announcement.objects.create(property=p, title=title, content=content, posted_by=request.user)
            messages.success(request, "Posted to all properties.")
        else:
            p = get_object_or_404(Property, id=property_id, organization=org)
            Announcement.objects.create(property=p, title=title, content=content, posted_by=request.user)
            messages.success(request, "Announcement posted.")
        return redirect('property:pm_dashboard')
        
    properties = Property.objects.filter(organization=org)
    return render(request, 'pm_create_announcement.html', {'properties': properties})

# ==========================================
# 4. LANDLORD BI DASHBOARD
# ==========================================
@login_required
@role_required(['HO'])
def ho_dashboard_view(request):
    # 1. Base Queryset
    my_units = Unit.objects.filter(owner=request.user).select_related('property', 'current_tenant')
    # 2. Parking Lots
    owned_parking = ParkingLot.objects.filter(owner=request.user).select_related('property', 'current_tenant')
    
    # 3. Aggregations
    total_units_count = my_units.count()
    active_leases = my_units.filter(current_tenant__isnull=False).count()
    vacant_units = total_units_count - active_leases
    
    occupancy_rate = 0
    if total_units_count > 0:
        occupancy_rate = int((active_leases / total_units_count) * 100)

    # 4. Financials
    all_invoices = Invoice.objects.filter(unit__in=my_units).order_by('-due_date')
    pending_amount = all_invoices.filter(is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
    net_income = all_invoices.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Collection Rate (This Month)
    today = timezone.now()
    month_invoices = all_invoices.filter(due_date__month=today.month, due_date__year=today.year)
    total_due_month = month_invoices.aggregate(Sum('amount'))['amount__sum'] or 0
    collected_month = month_invoices.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    
    collection_rate = 0
    if total_due_month > 0:
        collection_rate = int((collected_month / total_due_month) * 100)

    properties_count = my_units.values('property').distinct().count()
    locked_units = my_units.filter(is_locked=True)
    
    context = {
        'owned_units': my_units,
        'owned_parking': owned_parking,
        'invoices': all_invoices,
        'properties_count': properties_count,
        'total_units': total_units_count,
        'active_leases': active_leases,
        'vacant_units': vacant_units,
        'occupancy_rate': occupancy_rate,
        'collection_rate': collection_rate,
        'pending_amount': pending_amount,
        'net_income': net_income,
        'locked_units': locked_units,
    }
    return render(request, 'ho_dashboard.html', context)

@login_required
@role_required(['HO'])
def ho_assign_tenant_view(request):
    my_units = Unit.objects.filter(owner=request.user)
    if request.method == 'POST':
        unit_id = request.POST.get('unit_id')
        username = request.POST.get('tenant_username')
        try:
            unit = my_units.get(id=unit_id)
            tenant = CustomUser.objects.get(username=username, role='T')
            if Unit.objects.filter(current_tenant=tenant).exists():
                messages.error(request, "Tenant already assigned elsewhere.")
            else:
                unit.current_tenant = tenant
                unit.save()
                messages.success(request, f"Assigned {tenant.username}.")
        except Exception:
            messages.error(request, "Invalid Unit or Username.")
        return redirect('property:ho_dashboard')
    return render(request, 'ho_assign_tenant.html', {'units': my_units})

# ==========================================
# 5. SECURITY & RENTALS
# ==========================================
@login_required
@role_required(['SEC', 'PM'])
def security_desk_view(request):
    org = get_user_organization(request.user)
    # Active visitors are those with entry time but no exit time, and are marked active
    active_visitors = VisitorLog.objects.filter(
        unit__property__organization=org,
        is_active=True
    ).order_by('-entry_time')
    
    context = {
        'organization_name': org.name if org else 'Unassigned',
        'active_visitors': active_visitors
    }
    return render(request, 'security_desk.html', context)

@login_required
@role_required(['SEC', 'PM'])
def log_visitor_view(request):
    org = get_user_organization(request.user)
    if request.method == 'POST':
        unit_number = request.POST.get('unit_number')
        visitor_name = request.POST.get('visitor_name')
        visitor_id = request.POST.get('visitor_id')
        visitor_phone = request.POST.get('visitor_phone')
        visitor_type = request.POST.get('visitor_type')
        action = request.POST.get('action')
        id_collected = request.POST.get('id_collected') == 'on'
        
        try:
            unit = Unit.objects.filter(property__organization=org, unit_number__iexact=unit_number).first()
            if not unit:
                messages.error(request, f"Unit {unit_number} not found.")
                return redirect('property:security_desk')

            allowed = (action == 'ALLOW')
            notes = "Sent up" if allowed else "Waiting at gate"
            
            VisitorLog.objects.create(
                unit=unit,
                visitor_name=visitor_name,
                visitor_id_number=visitor_id,
                visitor_phone=visitor_phone,
                id_collected_at_gate=id_collected,
                visitor_type=visitor_type,
                notified_tenant=unit.current_tenant,
                allowed_entry=allowed,
                notes=notes,
                is_active=allowed
            )
            
            if unit.current_tenant:
                Notification.objects.create(
                    recipient=unit.current_tenant, 
                    message=f"{visitor_type}: {visitor_name} is at gate.", 
                    sender=request.user
                )
                messages.success(request, "Visitor logged and tenant notified.")
            
            return redirect('property:security_desk')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('property:security_desk')

@login_required
@role_required(['SEC', 'PM'])
def exit_visitor_view(request, visitor_id):
    visitor = get_object_or_404(VisitorLog, id=visitor_id)
    visitor.exit_time = timezone.now()
    visitor.is_active = False
    visitor.save()
    msg = f"{visitor.visitor_name} checked out."
    if visitor.id_collected_at_gate: msg += f" ⚠️ RETURN ID CARD: {visitor.visitor_id_number}"
    messages.success(request, msg)
    return redirect('property:security_desk')

@login_required
@role_required(['SEC', 'PM'])
def rental_checkin_view(request):
    org = get_user_organization(request.user)
    if request.method == 'POST':
        form = CheckInForm(request.POST, request.FILES)
        if form.is_valid():
            stay = form.save(commit=False)
            stay.unit = form.cleaned_data['unit_number'] # Cleaned in form
            
            if stay.unit.property.organization != org:
                messages.error(request, "Unit mismatch.")
                return redirect('property:rental_checkin')

            stay.checked_in_by = request.user
            stay.save()
            messages.success(request, f"Checked in {stay.guest_name}.")
            return redirect('property:rental_checkout_list')
    else:
        form = CheckInForm()
    return render(request, 'rental_checkin.html', {'form': form})

@login_required
@role_required(['SEC', 'PM'])
def rental_checkout_list_view(request):
    org = get_user_organization(request.user)
    active_stays = ShortTermStay.objects.filter(unit__property__organization=org, is_active=True)
    return render(request, 'rental_checkout_list.html', {'stays': active_stays})

@login_required
@role_required(['SEC', 'PM'])
def rental_process_checkout_view(request, stay_id):
    stay = get_object_or_404(ShortTermStay, id=stay_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=stay)
        if form.is_valid():
            stay = form.save(commit=False)
            stay.is_active = False
            stay.check_out_time = timezone.now()
            stay.save()
            messages.success(request, "Guest checked out.")
            return redirect('property:rental_checkout_list')
    else:
        form = FeedbackForm(instance=stay)
    return render(request, 'rental_process_checkout.html', {'stay': stay, 'form': form})

# ==========================================
# 6. TENANT & INVOICING (Updated Payment Logic)
# ==========================================

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

        # 2. PAYMENT ROUTING ENGINE
        # Find the organization linked to this invoice
        org = invoice.unit.property.organization
        
        # Fetch their payment configuration
        try:
            config = PaymentConfiguration.objects.get(organization=org, is_configured=True)
        except PaymentConfiguration.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'Property Manager has not configured payments yet.'}, status=400)

        # 3. Initiate STK Push (Using AGENCY Credentials)
        response = lipa_na_mpesa_online(
            phone_number=phone_number,
            amount=invoice.amount,
            account_reference=f"INV-{invoice.id}",
            transaction_desc=f"Payment for Invoice #{invoice.id}",
            # DYNAMIC KEYS PASSED HERE:
            consumer_key=config.consumer_key,
            consumer_secret=config.consumer_secret,
            business_shortcode=config.business_shortcode,
            passkey=config.passkey
        )
        
        if 'ResponseCode' in response and response['ResponseCode'] == '0':
            # SUCCESS: Store CheckoutRequestID for callback tracking
            invoice.checkout_request_id = response.get('CheckoutRequestID')
            invoice.save()
            
            return JsonResponse({'status': 'success', 'message': 'STK Push sent. Check your phone.'})
        else:
            error_msg = response.get('errorMessage', 'Failed to initiate payment.')
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)

    except Invoice.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invoice not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def mpesa_callback(request):
    """
    Central Callback Listener.
    Identifies the Invoice using CheckoutRequestID and marks it as paid.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            
            if result_code == 0:
                # Payment Successful
                try:
                    # FIND INVOICE BY CHECKOUT ID
                    invoice = Invoice.objects.get(checkout_request_id=checkout_request_id)
                    
                    if not invoice.is_paid:
                        invoice.is_paid = True
                        invoice.payment_date = timezone.now()
                        invoice.mpesa_code = stk_callback.get('CallbackMetadata', {}).get('Item', [])[1].get('Value') # Extract Receipt No roughly
                        invoice.save()
                        print(f"Invoice #{invoice.id} marked as PAID via Callback")
                        
                except Invoice.DoesNotExist:
                    print(f"Callback received for unknown CheckoutID: {checkout_request_id}")
            else:
                print(f"Payment Failed Callback: {stk_callback.get('ResultDesc')}")
                
        except Exception as e:
            print(f"Callback Error: {e}")
            
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@login_required
@role_required(['T'])
def tenant_dashboard_view(request):
    try:
        unit = Unit.objects.get(current_tenant=request.user)
        announcements = Announcement.objects.filter(property=unit.property, is_active=True).order_by('-created_at')
        my_tickets = Ticket.objects.filter(unit=unit).order_by('-created_at')
        my_invoices = Invoice.objects.filter(unit=unit).order_by('-due_date')
    except Unit.DoesNotExist:
        unit = None; announcements = []; my_tickets = []; my_invoices = []
    
    try: parking = ParkingLot.objects.get(current_tenant=request.user)
    except ParkingLot.DoesNotExist: parking = None
        
    context = {
        'unit': unit, 'parking': parking,
        'announcements': announcements, 'my_tickets': my_tickets, 'my_invoices': my_invoices,
    }
    return render(request, 'tenant_dashboard.html', context)

@login_required
@role_required(['T'])
def create_ticket_view(request):
    try:
        tenant_unit = Unit.objects.get(current_tenant=request.user)
    except Unit.DoesNotExist:
        return render(request, 'base.html', {'error': 'No unit.'})

    if request.method == 'POST':
        Ticket.objects.create(
            unit=tenant_unit,
            submitted_by=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            priority=request.POST.get('priority')
        )
        return redirect('property:tenant_dashboard')
    return render(request, 'ticket_create.html')

@login_required
def invoice_detail_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    # Simple permission check (can refine later)
    if request.user in [invoice.unit.owner, invoice.unit.current_tenant] or request.user.role in ['PM', 'ADMIN']:
        return render(request, 'invoice_pdf.html', {'invoice': invoice})
    messages.error(request, "Access denied.")
    return redirect('home')

# --- API ENDPOINTS (Simplified for brevity) ---
@login_required
def security_desk_notify_api(request): return JsonResponse({'status': 'ok'})
@login_required
def get_unread_notifications_api(request): 
    # Return count for polling
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count, 'notifications': []}) 
@login_required
def ho_assign_parking_api(request): return JsonResponse({'status': 'ok'})
@login_required
def mark_invoice_paid_api(request): return JsonResponse({'status': 'ok'})
@login_required
def tenant_pay_invoice_api(request): return JsonResponse({'status': 'ok'})
@login_required
def unit_details_view(request, unit_id): return render(request, 'unit_details.html')
@login_required
def property_details_view(request, property_id): return render(request, 'property_details.html')
@login_required
def invoice_admin_view(request): return render(request, 'invoice_admin.html')
@login_required
def ho_create_rent_invoice_view(request): return redirect('property:ho_dashboard')
@login_required
def bulk_create_units_view(request): return redirect('property:pm_dashboard')

# --- DEMO SEEDER ---
def seed_data_view(request):
    if CustomUser.objects.filter(username='david.kamau').exists():
        return HttpResponse("Data already seeded.")
    try:
        org = Organization.objects.create(name="Nairobi Estates Ltd", address="Westlands", contact_email="admin@nairobi.co.ke")
        CustomUser.objects.create_user(username="david.kamau", password="pass123", role='PM', organization=org)
        ho = CustomUser.objects.create_user(username="grace.wanjiku", password="pass123", role='HO')
        tenant = CustomUser.objects.create_user(username="brian.omondi", password="pass123", role='T')
        CustomUser.objects.create_user(username="juma.kevin", password="pass123", role='SEC', organization=org)
        CustomUser.objects.create_superuser(username="admin", email="admin@luxia.com", password="pass123")
        
        prop = Property.objects.create(name="Greenwood Residency", organization=org)
        unit = Unit.objects.create(property=prop, block="A", floor="1", door_number="04", owner=ho, current_tenant=tenant)
        Invoice.objects.create(unit=unit, amount=25000, due_date=datetime.date.today(), sender_role='LANDLORD')
        
        return HttpResponse("Seeded: david.kamau, grace.wanjiku, brian.omondi, juma.kevin (pass123)")
    except Exception as e: return HttpResponse(f"Error: {e}")

# ==========================================
# 7. FINANCE & OPERATIONS (NEW)
# ==========================================

@login_required
@role_required(['PM', 'CT'])
def record_meter_reading_view(request):
    """
    Caretaker/PM records water reading. System auto-generates invoice.
    """
    org = get_user_organization(request.user)
    
    if request.method == 'POST':
        form = MeterReadingForm(request.POST, request.FILES)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            if unit.property.organization != org:
                messages.error(request, "Unit not in your organization.")
                return redirect('property:record_reading')

            # 1. Get/Create Meter
            meter, _ = Meter.objects.get_or_create(unit=unit, meter_type='WATER', defaults={'meter_number': f'M-{unit.unit_number}'})
            
            # 2. Calculate Bill
            prev = form.cleaned_data['previous_reading']
            curr = form.cleaned_data['current_reading']
            consumption = curr - prev
            rate = unit.property.water_unit_cost
            bill = consumption * rate
            
            # 3. Create Reading
            reading = form.save(commit=False)
            reading.meter = meter
            reading.previous_reading = prev
            reading.consumption = consumption
            reading.bill_amount = bill
            reading.recorded_by = request.user
            
            # 4. Auto-Create Invoice
            invoice = Invoice.objects.create(
                unit=unit,
                amount=bill,
                due_date=timezone.now().date() + datetime.timedelta(days=7),
                description=f"Water Bill: {prev}-{curr} ({consumption} units)",
                sender_role='ORGANIZATION',
                is_paid=False
            )
            reading.invoice = invoice
            reading.save()
            
            messages.success(request, f"Recorded! Consumption: {consumption}. Bill: KES {bill}. Invoice sent.")
            return redirect('property:record_reading')
    else:
        form = MeterReadingForm()
        
    return render(request, 'finance_reading.html', {'form': form})

@login_required
@role_required(['PM'])
def log_expense_view(request):
    """
    Digital Petty Cash for PMs.
    """
    org = get_user_organization(request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            # Link to the first property found for now (Enhancement: Add Property Select to form)
            prop = Property.objects.filter(organization=org).first() 
            if not prop:
                messages.error(request, "No property found.")
                return redirect('property:pm_dashboard')
                
            expense.property = prop
            expense.recorded_by = request.user
            expense.save()
            messages.success(request, "Expense recorded successfully.")
            return redirect('property:financial_report')
    else:
        form = ExpenseForm()
        # Filter categories by Org
        form.fields['category'].queryset = ExpenseCategory.objects.filter(organization=org)
        
    return render(request, 'finance_expense.html', {'form': form})

@login_required
@role_required(['PM'])
def financial_report_view(request):
    """
    The 'One-Click Report' Dashboard.
    Aggregates Income vs Expenses.
    """
    org = get_user_organization(request.user)
    
    # Date Filter (Default: Current Month)
    today = timezone.now()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # 1. Income (Paid Invoices)
    income_qs = Invoice.objects.filter(
        unit__property__organization=org,
        is_paid=True,
        payment_date__month=month,
        payment_date__year=year
    )
    total_income = income_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 2. Expenses
    expense_qs = Expense.objects.filter(
        property__organization=org,
        date_incurred__month=month,
        date_incurred__year=year
    )
    total_expense = expense_qs.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # 3. Net
    net_profit = total_income - total_expense
    
    # 4. Breakdown
    expenses_by_cat = expense_qs.values('category__name').annotate(total=Sum('amount'))
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'expenses_breakdown': expenses_by_cat,
        'month': month, 'year': year,
        'recent_expenses': expense_qs.order_by('-date_incurred')[:10]
    }
    return render(request, 'finance_dashboard.html', context)