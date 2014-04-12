# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import requests

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
