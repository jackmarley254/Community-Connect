from django.urls import path
from . import views

app_name = 'property'

urlpatterns = [
    # --- DASHBOARDS ---
    path('pm/', views.pm_dashboard_view, name='pm_dashboard'),
    path('ho/', views.ho_dashboard_view, name='ho_dashboard'),
    path('tenant/', views.tenant_dashboard_view, name='tenant_dashboard'),
    path('security/', views.security_desk_view, name='security_desk'),

    # --- FEATURES ---
    # Tenant: Create Maintenance Ticket
    path('tenant/create-ticket/', views.create_ticket_view, name='create_ticket'),
    
    # PM: Bulk Unit Creator (The missing path causing your error)
    path('pm/units/bulk-create/', views.bulk_create_units_view, name='bulk_create_units'),
    
    # PM/Admin: Invoice Administration
    path('admin/invoices/', views.invoice_admin_view, name='invoice_admin'),
    
    # HO: Create Rent Invoice
    path('ho/invoice/create-rent/', views.ho_create_rent_invoice_view, name='ho_create_rent_invoice'),

    # --- APIs (AJAX Requests) ---
    path('api/notify/', views.security_desk_notify_api, name='security_desk_notify_api'),
    path('api/notifications/unread/', views.get_unread_notifications_api, name='get_unread_notifications_api'),
    path('api/ho/assign_parking/', views.ho_assign_parking_api, name='ho_assign_parking_api'),
    path('api/admin/mark-paid/', views.mark_invoice_paid_api, name='mark_invoice_paid_api'),
    path('api/tenant/pay-invoice/', views.tenant_pay_invoice_api, name='tenant_pay_invoice_api'),
    path('api/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    # Property Details View (List of Landlords & Payments)
    path('pm/property/<int:property_id>/', views.property_details_view, name='property_details'),
]