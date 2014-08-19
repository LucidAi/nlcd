# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nlcd.local")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()