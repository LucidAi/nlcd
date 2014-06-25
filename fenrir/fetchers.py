# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import logging

import requests
import grequests


class PageFetcher(object):

    DEFAULT_ENCODING = "utf-8"

    def __init__(self, encoding):
        self.encoding = encoding or self.DEFAULT_ENCODING

    def fetch(self, url):
        response = requests.get(url)
        return self.response_to_utf_8(response)

    def response_to_utf_8(self, response):
        try:
            response.encoding = self.encoding
            return response.text.encode("utf-8")
        except Exception:
            logging.warning("Unable to UTF-8 text from %r." % response.url)
            return ""

    def fetch_documents(self, urls, max_threads=1, timeout=10):
        return grequests.map((grequests.get(u, timeout=timeout) for u in urls), size=max_threads)