"""Configuración de Talenvía: prototipo académico ODS 10."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")
_DEV_SECRET = "django-insecure-talenvia-only-for-local-development"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", _DEV_SECRET)
if not DEBUG and SECRET_KEY == _DEV_SECRET:
    raise ImproperlyConfigured("Configura DJANGO_SECRET_KEY antes de activar producción.")
ALLOWED_HOSTS = [v.strip() for v in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if v.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "empleo.apps.EmpleoConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
# SQL Server es la base de datos principal. SQLite solo se usa como respaldo
# durante pruebas aisladas o para exportar una base local anterior.
DB_ENGINE = os.getenv("DB_ENGINE", "sqlserver").strip().lower()
if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DB_ENGINE in ("sqlserver", "mssql"):
    db_auth = os.getenv("DB_AUTH", "windows").strip().lower()
    if db_auth not in ("windows", "sqlserver"):
        raise ImproperlyConfigured("DB_AUTH debe ser 'windows' o 'sqlserver'.")
    extra_params = "Encrypt=yes"
    trust_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "false").lower() in ("true", "yes", "1")
    if trust_cert:
        if not DEBUG:
            raise ImproperlyConfigured(
                "DB_TRUST_SERVER_CERTIFICATE=true solo se permite en desarrollo local."
            )
        extra_params += ";TrustServerCertificate=yes"
    else:
        extra_params += ";TrustServerCertificate=no"
    db_config = {
        "ENGINE": "mssql",
        "NAME": os.getenv("DB_NAME", "TalenviaDB"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", ""),
        "OPTIONS": {
            "driver": os.getenv("DB_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
            "extra_params": extra_params,
        },
        "CONN_MAX_AGE": 0,
    }
    if db_auth == "sqlserver":
        db_user = os.getenv("DB_USER", "").strip()
        db_password = os.getenv("DB_PASSWORD", "")
        if not db_user or not db_password:
            raise ImproperlyConfigured(
                "Define DB_USER y DB_PASSWORD en tu .env local para autenticación SQL Server."
            )
        db_config.update({"USER": db_user, "PASSWORD": db_password})
    # Con DB_AUTH=windows, omitir USER/PASSWORD permite Trusted_Connection en Windows.
    DATABASES = {"default": db_config}
else:
    raise ImproperlyConfigured("DB_ENGINE debe ser 'sqlserver' o 'sqlite'.")
AUTH_USER_MODEL = "empleo.Usuario"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# No exponer private_uploads por URL, ni añadir una ruta media pública.
MEDIA_ROOT = BASE_DIR / "private_uploads"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "panel"
LOGOUT_REDIRECT_URL = "inicio"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "true").lower() == "true"
