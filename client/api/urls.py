# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls import patterns

from django.shortcuts import redirect
from django.views.generic.base import RedirectView


urlpatterns = patterns("client.api.views",
    url(r"get_article/$",   "get_article",      name="get_article"),
    url(r"get_segments/$",  "get_segments",     name="get_segments"),
    url(r"find_related/$",  "find_related",     name="find_related"),
)
