# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import logging

import requests
import grequests


class PageFetcher(object):

    DEFAULT_ENCODING = "utf-8"
    DEFAULT_TIMEOUT = 60

    def __init__(self, encoding=DEFAULT_ENCODING):
        self.encoding = encoding

    def fetch(self, url):
        response = requests.get(url)
        return self.response_to_utf_8(response)

    def fetch_urls(self, url2html_dict, max_threads=8, timeout=DEFAULT_TIMEOUT, del_on_error=True):
        def insert_html(response):
            if response is None:
                return
            if response.history is not None and len(response.history) > 0:
                original_url = response.history[0].url
            else:
                original_url = response.url
            try:
                html = self.response_to_utf_8(response)
                url2html_dict[original_url] = html
            except Exception:
                logging.warn("Saving HTML from %r. Error." % original_url)
        responses = self.fetch_documents(url2html_dict.iterkeys(), max_threads, timeout)
        map(insert_html, responses)
        for k, v in url2html_dict.items():
            if v is None:
                del url2html_dict[k]
        return responses

    def response_to_utf_8(self, response):
        try:
            response.encoding = self.encoding
            return response.text.encode("utf-8")
        except Exception:
            logging.warning("Unable to UTF-8 text from %r." % response.url)
            return ""

    def fetch_documents(self, urls, max_threads=1, timeout=DEFAULT_TIMEOUT):
        return grequests.map((grequests.get(u, timeout=timeout) for u in urls), size=max_threads)