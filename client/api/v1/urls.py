# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls import patterns

from django.shortcuts import redirect
from django.views.generic.base import RedirectView


urlpatterns = patterns("client.api.v1.views",
    url(r"get_test_graph/$", "get_test_graph", name="get_test_graph"),
)
