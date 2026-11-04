import ipaddress
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
from urllib.parse import quote

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_TIMEOUT = 10
TEAM_EMAIL = os.getenv('TEAM_EMAIL', EMAIL_HOST_USER)

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

SECURE_COOKIES = os.getenv('SECURE_COOKIES', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,172.25.90.121,172.27.72.167,172.29.57.63').split(',')
WS_ALLOWED_ORIGINS = [o for o in os.getenv('WS_ALLOWED_ORIGINS', '').split(',') if o]

MODEL_SERVER_URL = os.getenv('MODEL_SERVER_URL', 'http://127.0.0.1:8001')

CAMERA_MEDIA_ROOT = Path(os.getenv('CAMERA_MEDIA_ROOT', BASE_DIR / 'parking' / 'Data'))
CAMERA_NETWORKS = [ipaddress.ip_network(n.strip()) for n in os.getenv('CAMERA_NETWORKS', '').split(',') if n.strip()]
os.environ.setdefault('OPENCV_FFMPEG_CAPTURE_OPTIONS', 'protocol_whitelist;file,crypto,tcp,tls,udp,rtp,rtsp,http,https')

INSTALLED_APPS = [
    'camera',
    'channels',
    'users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'parking',
    'detection',
    'public',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]
ASGI_APPLICATION = 'smart_parking.asgi.application'

SIMPLE_JWT = {
    'BLACKLIST_AFTER_ROTATION': True,
    'ROTATE_REFRESH_TOKENS': True,
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=24),
    'CHECK_REVOKE_TOKEN': True,
}

REDIS_URL = f"redis://:{quote(os.getenv('REDIS_PASSWORD', ''), safe='')}@{os.getenv('REDIS_HOST', '172.27.72.167')}:{os.getenv('REDIS_PORT', '6379')}"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
    },
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smart_parking.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'smart_parking.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'sslmode': os.getenv('DB_SSLMODE', 'require'),
            'connect_timeout': 5,
            'sslrootcert': os.getenv('DB_SSL_ROOT_CERT'),
            'pool': {'min_size': 1, 'max_size': int(os.getenv('DB_POOL_SIZE', '10')), 'timeout': 10},
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
PARKING_TIME_ZONE = os.getenv('PARKING_TIME_ZONE', 'Africa/Algiers')
TRIAL_MONTHS = int(os.getenv('TRIAL_MONTHS', '3'))
GRACE_DAYS = int(os.getenv('GRACE_DAYS', '15'))
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'auth': '10/min',
        'register': '5/hour',
        'anon': os.getenv('PUBLIC_ANON_RATE', '30/min'),
        'user': os.getenv('PUBLIC_USER_RATE', '60/min'),
    },
    'NUM_PROXIES': int(os.getenv('NUM_PROXIES', '1')),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
