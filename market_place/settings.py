from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------
# Security
# ---------------------------------------------------
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-@z7*j5)%3_of%$68h_mfuyhxz4vnspr^_@f%n6i)p5+jd7!z&i')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# ---------------------------------------------------
# Cloudinary (must be early)
# ---------------------------------------------------
IS_RENDER = os.environ.get("RENDER", "").lower() == "true"
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
USE_CLOUDINARY = IS_RENDER and all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET])

# ---------------------------------------------------
# Installed apps
# ---------------------------------------------------
INSTALLED_APPS = [
    'channels',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',
    'drf_spectacular',
    'corsheaders',
    'marketplace',
    'widget_tweaks',
    'nested_admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_elasticsearch_dsl',
    'django.contrib.humanize'
]

if USE_CLOUDINARY:
    INSTALLED_APPS += ['cloudinary', 'cloudinary_storage']


ASGI_APPLICATION = 'Market_Place.asgi.application'

# Redis backend for WebSocket communication
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],  # change if your Redis runs elsewhere
        },
    },
}

# ---------------------------------------------------
# Middleware
# ---------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:55400",
#     "http://127.0.0.1:55400",
# ]
# Todo: only for dev
CORS_ALLOW_ALL_ORIGINS = True


ROOT_URLCONF = 'market_place.urls'

# ---------------------------------------------------
# Templates
# ---------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "marketplace" / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'marketplace.context_processors.navbar_counters',
            ],
            'builtins': ['django.templatetags.static'],
        },
    },
]

WSGI_APPLICATION = 'market_place.wsgi.application'

# ---------------------------------------------------
# Database
# ---------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://postgres:admin@localhost:5432/marketplace_db',
        conn_max_age=600
    )
}

# ---------------------------------------------------
# Password validation
# ---------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------
# Internationalization
# ---------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('ar', 'العربية'),
]

# ---------------------------------------------------
# Static & Media
# ---------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django 5.x: use STORAGES (DEFAULT_FILE_STORAGE/STATICFILES_STORAGE are ignored)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": (
        {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        }
        if USE_CLOUDINARY
        else {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": str(MEDIA_ROOT),
                "base_url": MEDIA_URL,
            },
        }
    ),
}

# ---------------------------------------------------
# Default primary key field type
# ---------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------
# Authentication
# ---------------------------------------------------
AUTH_USER_MODEL = 'marketplace.User'

# ---------------------------------------------------
# Login/logout redirects
# ---------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

LOCALE_PATHS = [BASE_DIR / 'locale']

# ---------------------------------------------------
# Elasticsearch
# ---------------------------------------------------
if IS_RENDER:
    ELASTICSEARCH_DSL = {'default': {'hosts': ''}}
    ELASTICSEARCH_DSL_AUTOSYNC = False
else:
    ELASTICSEARCH_DSL = {'default': {'hosts': 'http://localhost:9200'}}



REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Market Place API",
    "DESCRIPTION": "Full API matching all marketplace web app features (auth, items, categories, chat, notifications, etc.)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",
    "LICENSE": {"name": "Proprietary"},
    "CONTACT": {"email": "support@marketplace.com"},
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    # 👇 This tells SimpleJWT to use user.user_id instead of user.id
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_HEADER_TYPES': ('Bearer',),
}