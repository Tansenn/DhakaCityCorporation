"""
Django settings for the Dhaka South City Corporation service platform demo.

The demo is fully self-contained: SQLite, local static assets, simulated
notification outbox. No API keys or external services.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'GZP_SECRET_KEY',
    'django-insecure-gzp-adcelerete-demo-2026-do-not-use-in-production',
)
DEBUG = True
ALLOWED_HOSTS = ['*']

DEMO_MODE = True
APP_NAME = 'Dhaka South City Corporation: Integrated Digital Service Platform'
ORGANISATION = 'Dhaka South City Corporation'
SUPPLIER = 'Adcelerete Technologies Limited'
PAYMENT_GATEWAY_SECRET = os.environ.get(
    'GZP_GATEWAY_SECRET', 'demo-gateway-secret-gzp-2026'
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'organizations',
    'accounts',
    'workflow',
    'audit',
    'notifications',
    'facilities',
    'bookings',
    'payments',
    'hr',
    'documents',
    'projects',
    'meetings',
    'mis',
    'support',
    'services',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.DemoSessionMiddleware',
]

ROOT_URLCONF = 'gzp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'gzp.wsgi.application'
ASGI_APPLICATION = 'gzp.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 20},
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
LANGUAGES = [('en', 'English'), ('bn', 'বাংলা')]
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/app/'
LOGOUT_REDIRECT_URL = '/'

SESSION_COOKIE_AGE = 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = ["https://dhaka-city-corporation.adcelerete.com"]
LANGUAGE_COOKIE_NAME = 'gzp_lang'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
UPLOAD_MAX_MB = 5
UPLOAD_ALLOWED_EXT = {'.pdf', '.png', '.jpg', '.jpeg', '.csv', '.txt'}

# Demo support hours and response targets (business hours) - sample values
SUPPORT_TARGETS = {
    'Critical': 2,
    'High': 4,
    'Medium': 8,
    'Low': 16,
}

MESSAGE_TAGS = {
    10: 'debug', 20: 'info', 25: 'success', 30: 'warning', 40: 'danger',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}
