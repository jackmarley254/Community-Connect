from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # --- 1. THE MISSING LINK (Fixes 404 at /) ---
    # This tells Django: "When the path is empty, show the Splash Page"
    path('', views.splash_page_view, name='splash_page'),

    # --- 2. Authentication ---
    path('login/', views.login_view, name='auth_login'),
    path('logout/', views.logout_view, name='auth_logout'),
    path('register/', views.register_view, name='auth_register'),
    path('activation-pending/', views.activation_pending_view, name='activation_pending'),
]