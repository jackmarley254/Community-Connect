"""
URL configuration for community_connect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from property.views import dashboard_redirect_view  # <--- THIS IMPORT IS CRITICAL

urlpatterns = [
    path('admin/', admin.site.urls),

    # THIS LINE FIXES THE BLANK SCREEN:
    # It tells Django: "When at /home/, run the traffic cop function"
    path('home/', dashboard_redirect_view, name='home'),

    # Splash Page
    path('', include('users.urls')),

    # Auth & App
    path('auth/', include('users.urls')),
    path('app/', include('property.urls')),
]