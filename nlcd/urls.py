# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls import patterns

from django.shortcuts import redirect
from django.views.generic.base import RedirectView


urlpatterns = patterns("client.views",
    url(r"^$",      RedirectView.as_view(url="/app/", permanent=False)),
    url(r"^app/",  include("client.urls")),
    url(r"^api/",  include("client.api.urls")),
)
