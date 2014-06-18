# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import requests
import grequests


class PageFetcher(object):

    def __init__(self):
        pass

    @staticmethod
    def fetch(url):
        response = requests.get(url)
        return response.text

    @staticmethod
    def response_to_utf_8(response):
        try:
            response.encoding = "utf-8"
            return response.text.encode("utf-8")
        except Exception:
            return ""

    @staticmethod
    def fetch_documents(urls, max_threads=1):
        return grequests.map((grequests.get(u) for u in urls), size=max_threads)