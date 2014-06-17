# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import requests
import nltk.util
import grequests

from readability import readability


class PageFetcher(object):

    def __init__(self):
        pass

    @staticmethod
    def fetch(url):
        response = requests.get(url)
        return response.text

    @staticmethod
    def response_to_utf_8(response):
        response.encoding = "utf-8"
        return response.text.encode("utf-8")

    def fetch_document(self, url):
        html = self.fetch(url)
        doc = readability.Document(html)
        return doc

    def fetch_document_text(self, url):
        html = self.fetch(url)
        doc = readability.Document(html)
        summary = doc.summary()
        text = nltk.util.clean_html(summary)
        #text = " ".join(text.split())
        return text #"\n".join(text.split("\n"))

    @staticmethod
    def fetch_documents(urls, max_threads=1):
        return grequests.map((grequests.get(u) for u in urls), size=max_threads)

    @staticmethod
    def html_to_text(html):
        doc = readability.Document(html)
        summary = doc.summary()
        text = nltk.util.clean_html(summary)
        return text