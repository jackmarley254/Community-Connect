from django.urls import path
from . import views

app_name = 'property'

urlpatterns = [
    # --- CORE / SETUP ---
    path('setup-demo-data/', views.seed_data_view, name='seed_data'),

    # --- DASHBOARDS ---
    # New: Super Admin (SaaS Owner)
    path('super-admin/', views.super_admin_dashboard_view, name='super_admin_dashboard'),
    
    path('pm/', views.pm_dashboard_view, name='pm_dashboard'),
    path('ho/', views.ho_dashboard_view, name='ho_dashboard'),
    path('tenant/', views.tenant_dashboard_view, name='tenant_dashboard'),
    path('security/', views.security_desk_view, name='security_desk'),

    # --- PM MANAGEMENT ACTIONS ---
    # New: Add Users & Announcements
    path('pm/create-user/', views.pm_create_user_view, name='pm_create_user'),
    path('pm/create-announcement/', views.pm_create_announcement_view, name='pm_create_announcement'),
    path('pm/units/bulk-create/', views.bulk_create_units_view, name='bulk_create_units'),
    path('admin/invoices/', views.invoice_admin_view, name='invoice_admin'),
    path('pm/settings/', views.pm_settings_view, name='pm_settings'),
    
     # --- PM OPERATIONS ---
    path('pm/add-user/', views.pm_add_user_view, name='pm_add_user'),
    path('pm/add-property/', views.pm_add_property_view, name='pm_add_property'),
    path('pm/create-invoice/', views.pm_create_invoice_view, name='pm_create_invoice'),
    path('pm/post-announcement/', views.pm_post_announcement_view, name='pm_post_announcement'),
    path('pm/add-unit/', views.pm_add_unit_view, name='pm_add_unit'),
    # New Bulk Actions
    path('pm/units/bulk/', views.bulk_create_units_view, name='bulk_create_units'),
    path('pm/parking/bulk/', views.bulk_create_parking_view, name='bulk_create_parking'),
    path('pm/invoices/all/', views.pm_all_invoices_view, name='pm_all_invoices'),

    # --- LANDLORD (HO) ACTIONS ---
    # New: Assign Tenant to Unit
    path('ho/assign-tenant/', views.ho_assign_tenant_view, name='ho_assign_tenant'),
    path('ho/invoice/create-rent/', views.ho_create_rent_invoice_view, name='ho_create_rent_invoice'),

    # --- SECURITY & RENTALS (AIRBNB/VISITORS) ---
    # Short-Term Stays
    path('rentals/checkin/', views.rental_checkin_view, name='rental_checkin'),
    path('rentals/active/', views.rental_checkout_list_view, name='rental_checkout_list'),
    path('rentals/checkout/<int:stay_id>/', views.rental_process_checkout_view, name='rental_process_checkout'),
    
    # Visitor Log (Deliveries/Transient)
    path('visitor/log/', views.log_visitor_view, name='log_visitor'),
    path('visitor/exit/<int:visitor_id>/', views.exit_visitor_view, name='exit_visitor'),

    # --- FEATURES / TENANT ACTIONS ---
    path('tenant/create-ticket/', views.create_ticket_view, name='create_ticket'),

    # --- DETAIL VIEWS & PDFS ---
    path('invoice/<int:invoice_id>/', views.invoice_detail_view, name='invoice_detail'),
    path('pm/property/<int:property_id>/', views.property_details_view, name='property_details'),
    path('pm/unit/<int:unit_id>/', views.unit_details_view, name='unit_details'),

    # --- APIs (AJAX Requests) ---
    path('api/notify/', views.security_desk_notify_api, name='security_desk_notify_api'),
    path('api/notifications/unread/', views.get_unread_notifications_api, name='get_unread_notifications_api'),
    path('api/ho/assign_parking/', views.ho_assign_parking_api, name='ho_assign_parking_api'),
    path('api/admin/mark-paid/', views.mark_invoice_paid_api, name='mark_invoice_paid_api'),
    path('api/tenant/pay-invoice/', views.tenant_pay_invoice_api, name='tenant_pay_invoice_api'),
    path('api/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    # --- FINANCE & OPS ---
    path('finance/readings/', views.record_meter_reading_view, name='record_reading'),
    path('finance/expense/', views.log_expense_view, name='log_expense'),
    path('finance/report/', views.financial_report_view, name='financial_report'),
    path('finance/report/print/', views.financial_report_pdf_view, name='financial_report_print'),
]