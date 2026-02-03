from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # --- 1. THE MISSING LINK (Fixes 404 at /) ---
    # This tells Django: "When the path is empty, show the Splash Page"
    path('', views.splash_page_view, name='splash'),

    # --- 2. Authentication ---
    path('login/', views.login_view, name='auth_login'),
    path('logout/', views.logout_view, name='auth_logout'),
]