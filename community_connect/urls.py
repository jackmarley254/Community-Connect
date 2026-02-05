from django.contrib import admin
from django.urls import path, include
from property.views import dashboard_redirect_view
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect logged-in users
    path('home/', dashboard_redirect_view, name='home'),
    
    # ROOT URL -> Goes to users/urls.py (which now has the splash page)
    path('', include('users.urls')),
    
    path('auth/', include('users.urls')),
    path('app/', include('property.urls')),
]

# Allow serving uploaded ID photos during development/demo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)