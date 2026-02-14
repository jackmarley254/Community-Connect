from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # --- 2. Authentication ---
    path('login/', views.login_view, name='auth_login'),
    path('logout/', views.logout_view, name='auth_logout'),
    path('register/', views.register_view, name='auth_register'),
    path('activation-pending/', views.activation_pending_view, name='activation_pending'),
]