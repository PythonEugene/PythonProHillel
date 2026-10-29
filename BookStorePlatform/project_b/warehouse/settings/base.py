from pathlib import Path

import dj_database_url
import sentry_sdk
from celery.schedules import crontab
from decouple import Csv, config
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'users.apps.UsersConfig',
    'stock.apps.StockConfig',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'warehouse.urls'
WSGI_APPLICATION = 'warehouse.wsgi.application'
AUTH_USER_MODEL = 'users.CustomUser'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
elif config('USE_POSTGRES', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = 'en'
LANGUAGES = [('en', 'English'), ('uk', 'Українська')]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static files ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'

# --- Redis cache (in-memory cache when REDIS_URL is not set) ---
# Redis databases: 3 = Celery, 4 = cache (ProjectA uses 0, 1 and 2)
REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': f'{REDIS_URL}/4',
            'KEY_PREFIX': 'warehouse',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'warehouse',
        }
    }

# --- REST framework and JWT ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/hour', 'user': '5000/hour'},
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'api.errors.handle_stock_errors',
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Warehouse API',
    'DESCRIPTION': (
        'Warehouse service of the bookstore platform: stock, reservations and reports.\n\n'
        'Authorization: get a token at `/api/token/`, press "Authorize" and paste the access token.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api',
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
}

# --- Warehouse business settings ---
RESERVATION_TTL_MINUTES = config('RESERVATION_TTL_MINUTES', default=30, cast=int)
LOW_STOCK_THRESHOLD = config('LOW_STOCK_THRESHOLD', default=5, cast=int)
REPORTS_DIR = BASE_DIR / 'reports'

# --- Email (console backend by default: messages are printed to the log) ---
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='warehouse@bookstore.local')

# --- Celery ---
CELERY_BROKER_URL = f'{REDIS_URL}/3' if REDIS_URL else 'memory://'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/3' if REDIS_URL else 'cache+memory://'
# Without Redis (local run, tests) tasks are executed synchronously
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=not REDIS_URL, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    'expire-old-reservations': {
        'task': 'stock.tasks.expire_reservations',
        'schedule': crontab(minute='*/5'),
    },
    'daily-stock-report': {
        'task': 'stock.tasks.generate_daily_report',
        'schedule': crontab(hour=23, minute=50),
    },
}

# --- Logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': config('LOG_LEVEL', default='INFO')},
}

# --- Sentry (enabled only when SENTRY_DSN is set and SENTRY_ENABLED=1) ---
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN and config('SENTRY_ENABLED', default=False, cast=bool):
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        environment=config('SENTRY_ENVIRONMENT', default='development'),
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
