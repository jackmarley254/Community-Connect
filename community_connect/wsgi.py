import os
import sys
from django.core.wsgi import get_wsgi_application

# --- FIX: Add project root to Python Path ---
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)
# ------------------------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'community_connect.settings')

application = get_wsgi_application()