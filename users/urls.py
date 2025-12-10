from django.urls import path
from . import views

# Define the app namespace
app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='auth_login'),
    path('logout/', views.logout_view, name='auth_logout'),
]
    # Note: 'home' is defined in the project's root urls.py