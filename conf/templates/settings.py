# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import json
import datetime

try:
    from psycopg2cffi import compat
    compat.register()
except ImportError:
    pass


def project_dir(dir_name):
    return os.path.join(os.path.dirname(__file__), "..", dir_name)\
        .replace("\\", "//")

SECRET_KEY      = "h8(e(u3#k)l802(4mfh^f&&jp!@p*s#98tf++l#z-e83(#$x@*"
DEBUG           = {{webapp.service.debug}}
TEMPLATE_DEBUG  = {{webapp.service.debug}}
ALLOWED_HOSTS   = ["*"]


INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.admin",
    "rest_framework",
    "client",
)


MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)


ROOT_URLCONF = "{{webapp.service.module}}.urls"
WSGI_APPLICATION = "{{webapp.service.module}}.wsgi.application"

LANGUAGE_CODE   = "en-us"
TIME_ZONE       = "America/Los_Angeles"
USE_I18N        = True
USE_L10N        = True
USE_TZ          = True


STATIC_ROOT = "/webapp/"
STATIC_URL = "/webapp/"
STATICFILES_DIRS = (project_dir("webapp"),)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

TEMPLATE_DIRS = (
    "webapp/templates",
)

LOGGING = {
    "version": 1,

    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {
            "format": "%(levelname)s %(message)s"
        },
    },

    "handlers": {

        "django-file": {
            "class":        "logging.handlers.RotatingFileHandler",
            "filename":     "{{webapp.service.django_log}}",
            "formatter":    "verbose",
            "backupCount":  32,
            "maxBytes":     1024 * 1024 * 128,
        },

        "apilog-file": {
            "class":        "logging.handlers.RotatingFileHandler",
            "filename":     "{{webapp.service.lucid_api_log}}",
            "formatter":    "verbose",
            "backupCount":  32,
            "maxBytes":     1024 * 1024 * 128,
        },

    },

    "loggers": {

        "django": {
            "handlers":     ["django-file"],
            "level":        "ERROR",
            "propagate":    True,
        },

        "apilog": {
            "handlers":     ["apilog-file"],
            "level":        "INFO",
            "propagate":    True
        },

    },
}


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.auth.Auth0Authentication",
    ),
}


# 8 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
