import os
import shutil
import tempfile
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-anonka-secret-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'testserver',
    '.vercel.app',
]
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'anonka.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]},
    },
]
WSGI_APPLICATION = 'anonka.wsgi.application'

DATABASE_URL = os.getenv('DATABASE_URL')
if os.getenv('VERCEL') and not DATABASE_URL:
    raise RuntimeError('DATABASE_URL is required on Vercel. Add a PostgreSQL connection string in Vercel Environment Variables.')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    local_database = BASE_DIR / 'db.sqlite3'
    if os.getenv('VERCEL'):
        writable_database = Path(tempfile.gettempdir()) / 'anonka.sqlite3'
        if not writable_database.exists() and local_database.exists():
            shutil.copyfile(local_database, writable_database)
        local_database = writable_database
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': local_database}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = 'media/'
MEDIA_ROOT = Path(tempfile.gettempdir()) / 'anonka-media' if os.getenv('VERCEL') else BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
if os.getenv('VERCEL'):
    # Vercel functions do not share the SQLite session database between instances.
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    VERCEL_URL = os.getenv('VERCEL_URL')
    CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']
    if VERCEL_URL:
        CSRF_TRUSTED_ORIGINS.append(f'https://{VERCEL_URL}')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SOCIALACCOUNT_PROVIDERS = {
    'google': {'APP': {'client_id': os.getenv('GOOGLE_CLIENT_ID', ''), 'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''), 'key': ''}},
    'facebook': {'APP': {'client_id': os.getenv('FACEBOOK_CLIENT_ID', ''), 'secret': os.getenv('FACEBOOK_CLIENT_SECRET', ''), 'key': ''}},
}
ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_SIGNUP_FIELDS = ['username*', 'password1*', 'password2*']
