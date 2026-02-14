from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

# 1. Import Views from your apps
from property.views import dashboard_redirect_view
from users.views import splash_page_view  # <--- Import the splash view here

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 2. Redirect logged-in users
    path('home/', dashboard_redirect_view, name='home'),
    
    # 3. ROOT URL -> Points directly to the view (Fixes the duplicate include)
    path('', splash_page_view, name='splash_page'),
    
    # 4. AUTH URLS -> Includes users.urls (e.g., /auth/login/)
    path('auth/', include('users.urls')),
    
    # 5. APP URLS
    path('app/', include('property.urls')),
]

# Allow serving uploaded ID photos during development/demo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)