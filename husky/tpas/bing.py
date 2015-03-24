# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import math
import urllib
import logging
import requests
import traceback

from husky.textutil import TextUtil



class BingAPI(object):
    BASE_URL = "https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Web?"

    def __init__(self, key):
        if key is None:
            raise ValueError("API key cannot be None")
        self.key = key
        self.config = None
        self.text_util = TextUtil()

    @staticmethod
    def from_config(api_config):

        print api_config

        api = BingAPI(key=api_config["account_key"])
        return api

    def make_query(self,
                     query_string=None,
                     ):
        q = {
            "Query"          : "'%s'" % query_string,
            "$format"        : "json",
            "$skip"          : "0",
        }
        for key, value in q.items():
            if value is None:
                del q[key]
        return q

    def make_query_pages(self, results_number=5, start=1):
        start = 1
        page_size = 50.0
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
                     query_size_heuristic=50):

        result_urls = []
        found_results = []
        total_results = None

        query_size = self.text_util.words_count(query["Query"])

        for start_index in self.make_query_pages(max_results):

            if total_results is not None and start_index > total_results:
                break

            query["$skip"] = start_index

            url = self.make_url(query)

            logging.debug(url)

            result_urls.append(url)

            try:
                api_response = requests.get(url, auth=(self.key, self.key)).json()
            except Exception:
                logging.error("Error while calling '%s':%s" % (url,  traceback.format_exc()))
                api_response = None

            if api_response is None or "d" not in api_response:
                logging.warn("API response is None")
                break

            api_response = api_response["d"]

            if "results" not in api_response or len(api_response["results"]) == 0:
                if total_results is None:
                    logging.warn("Items not found. Stop.")
                    break
                else:
                    logging.warn("Item not found. Skip.")
                    continue

            found_results.extend(api_response["results"])

            if len(api_response["results"]) < 50:
                break

        return found_results, result_urls, 0 if total_results is None else total_results

    def __repr__(self):
        return "<FarooAPI(key='%s')>" % self.key[:8] + ".."
