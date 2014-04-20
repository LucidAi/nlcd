# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>


from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls import patterns


urlpatterns = patterns("client.views",
    url(r"$", "app_html", name="app_html"),
)
