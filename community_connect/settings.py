from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================
# 1. CORE SETTINGS
# ==============================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed Hosts (Includes Render and Ngrok)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# ==============================================
# 2. INSTALLED APPS
# ==============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third Party
    'whitenoise',  # Handles static files in production
    
    # My Apps
    'users',
    'property',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # WHITENOISE MUST BE HERE (After SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'community_connect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # You can add os.path.join(BASE_DIR, 'templates') here if you have global templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'community_connect.wsgi.application'

# ==============================================
# 3. DATABASE (MySQL for Render/TiDB, SQLite for Local)
# ==============================================

# Check if we are running on Render (Render sets this env var automatically)
if config('RENDER', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default='4000'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                # TiDB requires SSL
                'ssl': {'ca': '/etc/ssl/certs/ca-certificates.crt'} 
            },
        }
    }
else:
    # Local Development -> SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ==============================================
# 4. AUTH & PASSWORDS
# ==============================================
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Point to our Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Login Redirects
LOGIN_URL = 'users:auth_login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'users:auth_login'

# ==============================================
# 5. STATIC FILES (WhiteNoise Configuration)
# ==============================================
STATIC_URL = 'static/'

# Where to collect files for deployment
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Enable WhiteNoise compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Extra places to look for static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ==============================================
# 6. DEFAULT PRIMARY KEY FIELD TYPE
# ==============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================
# 7. M-PESA DARAJA SETTINGS
# ==============================================
DARAJA_ENVIRONMENT = config('DARAJA_ENVIRONMENT', default='sandbox')

if DARAJA_ENVIRONMENT == 'production':
    DARAJA_API_URL = 'https://api.safaricom.co.ke'
else:
    DARAJA_API_URL = 'https://sandbox.safaricom.co.ke'

DARAJA_CONSUMER_KEY = config('DARAJA_CONSUMER_KEY', default='')
DARAJA_CONSUMER_SECRET = config('DARAJA_CONSUMER_SECRET', default='')
DARAJA_BUSINESS_SHORTCODE = config('DARAJA_BUSINESS_SHORTCODE', default='174379') 
DARAJA_PASSKEY = config('DARAJA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
DARAJA_CALLBACK_URL = config('DARAJA_CALLBACK_URL', default='http://localhost:8000/api/mpesa/callback/')