# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
import json


def project_dir(dir_name):
    return os.path.join(os.path.dirname(__file__), "..", dir_name)\
        .replace("\\", "//")

# with open(project_dir("conf/dev.json"), "rb") as fp:
#     CONF = json.load(fp)


SECRET_KEY = "h8(e(u3#k)l802(4mfh^f&&jp!@p*s#98tf++l#z-e83(#$x@*"
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = ["localhost"]


INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "client"
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "nlcd.urls"
WSGI_APPLICATION = "nlcd.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": project_dir("nlcd.db"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

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

    "handlers": {
        "logfile": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": "log.txt"
        },
    },

    "loggers": {

        "django": {
            "handlers": ["logfile"],
            "level": "DEBUG",
            "propagate": False,
        },

        "nlcd": {
            "handlers": ["logfile"],
            "level": "DEBUG",
            "propagate": False
        },
    },
}


FILE_UPLOAD_MAX_MEMORY_SIZE = 32 * 1024 * 1024