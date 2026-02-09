from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import dj_database_url

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "plantas.authentication.JWTCookieAuthentication",  # Primero cookies
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # Fallback
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)

# Permitir HTTP para OAuth solo en desarrollo
if DEBUG:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

ALLOWED_HOSTS = []

RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Agregamos el dominio personalizado
ALLOWED_HOSTS.extend(['riegum.com', 'www.riegum.com'])

# Application definition
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    # Nuestras apps primero para que sus plantillas tengan prioridad
    'plantas',
    'notificaciones',
    # Apps de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps de terceros
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de CORS
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True  # Necesario para cookies httpOnly
    # En desarrollo, confiamos en los orígenes locales para CSRF
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
else:
    # Empezamos con los dominios personalizados
    CORS_ALLOWED_ORIGINS = [
        "https://riegum.com",
        "https://www.riegum.com",
    ]
    CORS_ALLOW_CREDENTIALS = True  # Necesario para cookies httpOnly
    if RENDER_EXTERNAL_HOSTNAME:
        CORS_ALLOWED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
    # En producción, los orígenes de CSRF son los mismos que los de CORS
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

ROOT_URLCONF = 'riego_indoor.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'RIEGO-INDOOR' / 'templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
#]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 👈 Esto apunta al folder raíz "templates"
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


WSGI_APPLICATION = 'riego_indoor.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        # Lee la variable de entorno DATABASE_URL que inyecta Render.
        # Para desarrollo local, lee la misma variable desde tu archivo .env
        default=config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=not DEBUG  # Requerir SSL solo en producción (cuando DEBUG es False)
    )
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = "America/Argentina/Cordoba"

USE_I18N = True

USE_TZ = True

# =========================
# Google Cloud Storage (GCS)
# =========================

GCS_BUCKET_NAME = config('GCS_BUCKET_NAME', default='riegum.com')

# Configuración de credenciales según entorno
if DEBUG:
    # Desarrollo: usar archivo local
    GOOGLE_SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials', 'google-service-account.json')
else:
    # Producción: leer JSON desde variable de entorno y crear archivo temporal
    import json
    import tempfile
    
    gcs_credentials_json = config('GCS_SERVICE_ACCOUNT_JSON', default=None)
    
    if gcs_credentials_json:
        try:
            # Crear archivo temporal para google-cloud-storage
            gcs_cred_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            gcs_cred_file.write(gcs_credentials_json)
            gcs_cred_file.close()
            GOOGLE_SERVICE_ACCOUNT_FILE = gcs_cred_file.name
            print(f"✅ GCS credentials loaded from environment variable")
        except Exception as e:
            print(f"❌ Error al cargar credenciales GCS: {e}")
            GOOGLE_SERVICE_ACCOUNT_FILE = None
    else:
        print("⚠️ GCS_SERVICE_ACCOUNT_JSON no encontrada en producción")
        GOOGLE_SERVICE_ACCOUNT_FILE = None

# =========================
# Media Files (Desarrollo)
# =========================

if DEBUG:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de almacenamiento de estáticos dependiente del entorno.
# En producción (DEBUG=False), WhiteNoise se encarga de los estáticos.
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#STATICFILES_DIRS = [BASE_DIR / 'users' / 'static']

LOGIN_REDIRECT_URL = '/home/dashboard/'

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default=None)
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default=None)

GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY')

# --- Security Settings for Production ---
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- Email Configuration ---
if DEBUG:
    # En desarrollo, los emails se imprimen en la consola.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # En producción, si hay configuración de email, usar SMTP
    # Si no, usar console backend (los emails no se enviarán pero la app funcionará)
    email_host = config('EMAIL_HOST', default=None)
    
    if email_host:
        # Email configurado: usar SMTP
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_HOST = email_host
        EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
        EMAIL_USE_TLS = True
        EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
        EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
        DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@riegum.com')
        SERVER_EMAIL = DEFAULT_FROM_EMAIL
    else:
        # Email NO configurado: usar console backend (temporal hasta configurar SMTP)
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        DEFAULT_FROM_EMAIL = 'noreply@riegum.com'
        SERVER_EMAIL = DEFAULT_FROM_EMAIL


# --- Logging Configuration ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'riego_indoor.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'plantas': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'notificaciones': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO' if DEBUG else 'WARNING',
    },
}


# --- Sentry Configuration (Error Monitoring) ---
# Sentry se activa solo en producción y si se proporciona SENTRY_DSN
if not DEBUG:
    SENTRY_DSN = config('SENTRY_DSN', default=None)
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            
            # Porcentaje de transacciones a trackear para performance monitoring
            traces_sample_rate=0.1,  # 10% de requests
            
            # Enviar datos de performance
            profiles_sample_rate=0.1,  # 10% de requests
            
            # Información de release para tracking de versiones
            release=config('RENDER_GIT_COMMIT', default='unknown'),
            
            # Ambiente (producción)
            environment='production',
            
            # Enviar information del usuario con cada error
            send_default_pii=True,
        )

