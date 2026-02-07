from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def env_true(name: str, default="false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "y", "on")

# ---------------------------------------------------
# Security
# ---------------------------------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-@z7*j5)%3_of%$68h_mfuyhxz4vnspr^_@f%n6i)p5+jd7!z&i",
)
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# ---------------------------------------------------
# Cloudinary (must be early)
# ---------------------------------------------------
IS_RENDER = os.environ.get("RENDER", "").strip().lower() == "true"

# Detect Railway reliably (Railway sets at least one of these)
IS_RAILWAY = bool(
    os.getenv("RAILWAY_ENVIRONMENT")
    or os.getenv("RAILWAY_PROJECT_ID")
    or os.getenv("RAILWAY_SERVICE_ID")
)

# ✅ Goal:
# - Locally: DO NOT use cloudinary by default
# - Railway: use hardcoded cloudinary creds TEMPORARILY (until Railway env vars are trusted)
#
# Control flags:
# - FORCE_LOCAL_MEDIA=true  -> force local media storage even if cloudinary creds exist (default locally)
# - FORCE_CLOUDINARY=true   -> force cloudinary usage (useful for testing)
FORCE_LOCAL_MEDIA = env_true("FORCE_LOCAL_MEDIA", "true") and (not IS_RAILWAY)
FORCE_CLOUDINARY = env_true("FORCE_CLOUDINARY", "false")

# TEMP: hardcode creds on Railway only
if IS_RAILWAY:
    # ⚠️ IMPORTANT: put your NEW rotated secret here
    CLOUDINARY_CLOUD_NAME = "dljrdisnq"
    CLOUDINARY_API_KEY = "815862547747528"
    CLOUDINARY_API_SECRET = "PUT_YOUR_NEW_SECRET_HERE"
else:
    # Local/dev: read from env (but we still default to local storage unless you force cloudinary)
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

HAS_CLOUDINARY_CREDS = all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET])

# Decide if we use cloudinary
# - Railway: yes if creds exist (hardcoded) unless forced local
# - Local: no by default (FORCE_LOCAL_MEDIA true), unless FORCE_CLOUDINARY true
USE_CLOUDINARY = (
    HAS_CLOUDINARY_CREDS
    and (IS_RAILWAY or FORCE_CLOUDINARY)
    and (not FORCE_LOCAL_MEDIA)
)

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
        "API_KEY": CLOUDINARY_API_KEY,
        "API_SECRET": CLOUDINARY_API_SECRET,
    }
    CLOUDINARY_URL = (
        f"cloudinary://{CLOUDINARY_API_KEY}:{CLOUDINARY_API_SECRET}@{CLOUDINARY_CLOUD_NAME}"
    )

print("🔍 Cloudinary Debug:")
print("   IS_RAILWAY:", IS_RAILWAY)
print("   FORCE_LOCAL_MEDIA:", FORCE_LOCAL_MEDIA)
print("   FORCE_CLOUDINARY:", FORCE_CLOUDINARY)
print("   USE_CLOUDINARY result:", USE_CLOUDINARY)
print("   Credentials present:", HAS_CLOUDINARY_CREDS)
print(
    "   DEFAULT STORAGE BACKEND:",
    "cloudinary_storage.storage.MediaCloudinaryStorage"
    if USE_CLOUDINARY
    else "django.core.files.storage.FileSystemStorage",
)

# ---------------------------------------------------
# Installed apps
# ---------------------------------------------------
INSTALLED_APPS = [
    "channels",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",
    "marketplace",
    "widget_tweaks",
    "nested_admin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_elasticsearch_dsl",
    "django.contrib.humanize",
]

if USE_CLOUDINARY:
    INSTALLED_APPS = ["cloudinary_storage", "cloudinary"] + INSTALLED_APPS
    print("   ✅ Cloudinary apps added to INSTALLED_APPS")

ASGI_APPLICATION = "Market_Place.asgi.application"

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
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = "market_place.urls"

# ---------------------------------------------------
# Templates
# ---------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "marketplace" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "marketplace.context_processors.navbar_counters",
            ],
            "builtins": ["django.templatetags.static"],
        },
    },
]

WSGI_APPLICATION = "market_place.wsgi.application"

# ---------------------------------------------------
# Database
# ---------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default="postgres://postgres:admin@localhost:5432/marketplace_db",
        conn_max_age=600,
    )
}

# ---------------------------------------------------
# Password validation
# ---------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------
# Internationalization
# ---------------------------------------------------
LANGUAGE_CODE = "ar"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("ar", "العربية"),
]

# ---------------------------------------------------
# Static & Media
# ---------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django 5.x: use STORAGES (DEFAULT_FILE_STORAGE/STATICFILES_STORAGE are ignored)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": (
        {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}
        if USE_CLOUDINARY
        else {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": str(MEDIA_ROOT), "base_url": MEDIA_URL},
        }
    ),
}

# -------------------------------------------------------------------
# Compatibility shims for django-cloudinary-storage (expects old setting names)
# Fixes Railway crash: AttributeError: Settings has no STATICFILES_STORAGE
# -------------------------------------------------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
    if USE_CLOUDINARY
    else "django.core.files.storage.FileSystemStorage"
)

# ---------------------------------------------------
# Default primary key field type
# ---------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------
# Authentication
# ---------------------------------------------------
AUTH_USER_MODEL = "marketplace.User"

# ---------------------------------------------------
# Login/logout redirects
# ---------------------------------------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------
# Elasticsearch
# ---------------------------------------------------
if IS_RENDER:
    ELASTICSEARCH_DSL = {"default": {"hosts": ""}}
    ELASTICSEARCH_DSL_AUTOSYNC = False
else:
    ELASTICSEARCH_DSL = {"default": {"hosts": "http://localhost:9200"}}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login": "5/minute",
    },
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
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CSRF_TRUSTED_ORIGINS = [
    "https://market-place-rhjg.onrender.com",
    "http://localhost:8000",
    "https://web-production-c250.up.railway.app",
]

SESSION_COOKIE_HTTPONLY = True

X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 24

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs/marketplace.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": LOG_LEVEL},
        "marketplace": {"handlers": ["console", "file"], "level": "DEBUG"},
    },
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID", "")
