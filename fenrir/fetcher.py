# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import requests
import nltk.util

from readability import readability


class Fetcher(object):

    def __init__(self):
        pass

    def fetch(self, url):
        response = requests.get(url)
        return response.text

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
