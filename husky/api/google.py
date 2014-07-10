# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import math
import urllib
import logging
import requests
import traceback

from husky.textutil import TextUtil

class CseError(Exception):
    pass


class GoogleApiConfig(object):

    def __init__(self, api_config_dict):
        pass


class CseAPI(object):
    BASE_URL = "https://www.googleapis.com/customsearch/v1?"

    def __init__(self, key, engine_id):
        if key is None:
            raise CseError("API key cannot be None")
        self.key = key
        self.engine_id = engine_id
        self.config = None
        self.text_util = TextUtil()

    @staticmethod
    def from_config(api_config):
        api = CseAPI(key=api_config["googleApiKey"], engine_id=api_config["googleEngineId"])
        api.config = GoogleApiConfig(api_config)
        return api

    def make_query(self,
                     query_string=None,
                     country=None,
                     date_start=None,
                     date_end=None,
                     exact_terms=None,
                     ):
        q = {
            "q": query_string,

            "cr": country,                  # Country restrict(s)
            "dateRestrict": None,           # Specifies all search results are from a time period (string)
            "exactTerms": exact_terms,      # Identifies a phrase that all documents in the search results must
                                            # contain (string)
            "excludeTerms": None,           # Identifies a word or phrase that should not appear in any documents
                                            # in the search results (string)
            "fileType": None,               # Returns images of a specified type. Some of the allowed values are:
                                            # bmp, gif, png, jpg, svg, pdf, ... (string)
            "num": None,                    # Number of search results to return (integer),
            "orTerms": None,                # Provides additional search terms to check for in a document, where each
                                            # document in the search results must contain at least one of the additional
                                            # search terms (string)
            "relatedSite": None,            # Specifies that all search results should be pages that are related to the
                                            # specified URL (string)
            "sort": None,                   # The sort expression to apply to the results (string)
            "start": None,                  # The index of the first result to return (integer)

        }
        for key, value in q.items():
            if value is None:
                del q[key]
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

    def find_results(self, query,
                     max_results=1000,
                     upper_threshold=1000,
                     bottom_threshold=100,
                     query_size_heuristic=10):

        result_urls = []
        found_results = []
        total_results = None

        query_size = self.text_util.words_count(query["exactTerms"])

        for start_index in self.make_query_pages(max_results):

            if total_results is not None and start_index > total_results:
                break

            query["start"] = start_index
            url = self.make_cse_url(query) + "&cx=%s&key=%s" % (self.engine_id, self.key)

            try:
                api_response = requests.get(url).json()
            except Exception:
                logging.error("Error while calling '%s':%s" % (url,  traceback.format_exc()))
                api_response = None

            if api_response is None:
                logging.warn("API response is None")
                break

            if "searchInformation" not in api_response:
                logging.warn("Search information not found")
                break

            if total_results is None:
                total_results = int(api_response["searchInformation"]["totalResults"])

            if total_results > upper_threshold:
                logging.warn("Total results it too large %d" % total_results)
                break

            if total_results > bottom_threshold and query_size < query_size_heuristic:
                logging.warn("Too many results for too short query %d" % total_results)
                break

            if "items" not in api_response or len(api_response["items"]) == 0:
                logging.warn("Items not found.")
                break

            found_results.extend(api_response["items"])
            result_urls.append(url)

        return found_results, result_urls, 0 if total_results is None else total_results

    def __repr__(self):
        return "<CseAPI(key='%s', engine='%s')>" % (self.key[:8]+"..", self.engine_id[:8]+"..")
