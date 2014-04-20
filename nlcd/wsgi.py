# coding: utf-8

# Copyright (C) University of Southern California (http://usc.edu)
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE


import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nlcd.local")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()