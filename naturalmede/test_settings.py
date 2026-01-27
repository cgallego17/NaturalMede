"""
Configuración de Django para pruebas
"""
import os
from .settings import *

# Usar base de datos en memoria para pruebas más rápidas
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Configuración específica para pruebas
SECRET_KEY = 'test-secret-key-for-testing-only'

# Desactivar migraciones para pruebas más rápidas
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Configuración de logging para pruebas
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Configuración de archivos estáticos para pruebas
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Configuración de caché para pruebas
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Configuración de sesiones para pruebas
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Desactivar debug toolbar para pruebas
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')

# Configuración de email para pruebas
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Configuración de archivos de media para pruebas
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')

# Desactivar señales de auditoría durante pruebas
AUDIT_DISABLE_SIGNALS = True

# Configuración de timezone para pruebas
USE_TZ = True
TIME_ZONE = 'UTC'
