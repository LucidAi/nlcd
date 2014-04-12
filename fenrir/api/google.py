# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import math
import urllib
import logging
import requests
import traceback


class CseError(Exception): pass


class CseAPI(object):
    BASE_URL = "https://www.googleapis.com/customsearch/v1?"

    def __init__(self, key, engine_id):
        if key is None:
            raise CseError("API key cannot be None")
        self.key = key
        self.engine_id = engine_id

    def make_query(self,
                     query_string=None,
                     country=None,
                     date_start=None,
                     date_end=None,
                     terms=None,
                     ):
        q = {
            "q": query_string,

            "cr": country,          # Country restrict(s)
            "dateRestrict": None,   # Specifies all search results are from a time period (string)
            "exactTerms": None,     # Identifies a phrase that all documents in the search results must contain (string)
            "excludeTerms": None,   # Identifies a word or phrase that should not appear in any documents in the search
                                    # results (string)
            "fileType": None,       # Returns images of a specified type. Some of the allowed values are: bmp, gif,
                                    # png, jpg, svg, pdf, ... (string)
            "num": None,            # Number of search results to return (integer),
            "orTerms": None,        # Provides additional search terms to check for in a document, where each document
                                    # in the search results must contain at least one of the additional search
                                    # terms (string)
            "relatedSite": None,    # Specifies that all search results should be pages that are related to the
                                    # specified URL (string)
            "sort": None,           # The sort expression to apply to the results (string)
            "start": None,          # The index of the first result to return (integer)

            "cx": self.engine_id,
            "key": self.key,
        }
        for k, v in q.items():
            if v is None:
                del q[k]
        return q

    def make_query_pages(self, results_number=10, start=1):
        start = 1
        page_size = 10.0
        pages = math.ceil(float(results_number) / page_size)
        for page in xrange(int(pages)):
            yield int(page * page_size + 1)

    def make_cse_url(self, query):
        params = urllib.urlencode(query)
        return self.BASE_URL + params

    def find_results(self, query, number=10):
        for start_index in self.make_query_pages(number):
            query["start"] = start_index
            url = self.make_cse_url(query)
            try:
                logging.info("Calling %s" % url)
                items = requests.get(url).json()["items"]
                for item in items:
                    yield item
            except Exception:
                formatted = traceback.format_exc()
                logging.error("Error while calling '%s':%s" % (url, formatted))
