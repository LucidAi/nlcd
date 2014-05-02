# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import requests
import nltk.util
import grequests

from readability import readability


class Fetcher(object):

    def __init__(self):
        pass

    def fetch(self, url):
        response = requests.get(url)
        return response.text

    def response_to_utf_8(self, response):
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
        return text#"\n".join(text.split("\n"))

    def fetch_documents(self, urls, max_threads=1):
        return grequests.imap((grequests.get(u) for u in urls), size=max_threads)

    def html_to_text(self, html):
        doc = readability.Document(html)
        summary = doc.summary()
        text = nltk.util.clean_html(summary)
        return text