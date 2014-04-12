# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import urllib
import requests


class CseError(Exception): pass


class CseAPI(object):
    BASE_URL = "https://www.googleapis.com/customsearch/v1?"

    def __init__(self, key, engine_id):
        if key is None:
            raise CseError("API key cannot be None")
        self.key = key
        self.engine_id = engine_id

    def search(self, query_string):
        return self.execute_query({
            "q": query_string,
            "cx": self.engine_id,
            "key": self.key,
        })

    def execute_query(self, query):
        params = urllib.urlencode(query)
        return requests.get("%s%s" % (self.BASE_URL, params)).json()
