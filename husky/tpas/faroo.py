# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import math
import urllib
import logging
import requests
import traceback

from husky.textutil import TextUtil


class FarooAPI(object):
    BASE_URL = "http://www.faroo.com/api?"

    def __init__(self, key):
        if key is None:
            raise ValueError("API key cannot be None")
        self.key = key
        self.config = None
        self.text_util = TextUtil()

    @staticmethod
    def from_config(api_config):
        api = FarooAPI(key=api_config["api_key"])
        return api

    def make_query(self,
                     query_string=None,
                     length="10",
                     lang="en",
                     src="news"
                     ):
        q = {
            "q"             : query_string,
            "start"         : None,
            "length"        : length,
            "l"             : lang,
            "src"           : src,
            "f"             : "json",

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

    def make_url(self, query):
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

        query_size = self.text_util.words_count(query["q"])

        for start_index in self.make_query_pages(max_results):

            if total_results is not None and start_index > total_results:
                break

            query["start"] = start_index

            url = self.make_url(query) + "&key=%s" % self.key

            logging.debug(url)

            result_urls.append(url)

            try:
                api_response = requests.get(url).json()
            except Exception:
                logging.error("Error while calling '%s':%s" % (url,  traceback.format_exc()))
                api_response = None

            if api_response is None:
                logging.warn("API response is None")
                break

            if "count" not in api_response:
                logging.warn("Search information not found")
                if total_results is None:
                    break

            if total_results is None:
                total_results = int(api_response["count"])

            if total_results > upper_threshold:
                logging.warn("Total results it too large %d" % total_results)
                break

            if total_results > bottom_threshold and query_size < query_size_heuristic:
                logging.warn("Too many results for too short query %d" % total_results)
                break

            if "results" not in api_response or len(api_response["results"]) == 0:
                if total_results is None:
                    logging.warn("Items not found. Stop.")
                    break
                else:
                    logging.warn("Item not found. Skip.")
                    continue

            found_results.extend(api_response["results"])

        return found_results, result_urls, 0 if total_results is None else total_results

    def __repr__(self):
        return "<FarooAPI(key='%s')>" % self.key[:8] + ".."
