from decouple import Csv, config

from .base import *  # noqa: F401,F403

DEBUG = False

# No default on purpose: the server must not start with unsafe host settings.
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# WhiteNoise serves static files right after SecurityMiddleware.
MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,  # noqa: F405
    'whitenoise.middleware.WhiteNoiseMiddleware',
)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# HTTPS and security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_REDIRECT_EXEMPT = [r'^health/$']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=3600, cast=int)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Intentionally not enabled: the site lives on a subdomain of the hosting platform.
SILENCED_SYSTEM_CHECKS = ['security.W005', 'security.W021']
