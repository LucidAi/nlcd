# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import math
import urllib
import logging
import requests
import traceback

import urllib2
import oauth2 as oauth
import time

OAUTH_CONSUMER_KEY = "blahblahblah"
OAUTH_CONSUMER_SECRET = "blah"

def oauth_request(url, params, key, secret, method="GET"):
    params["oauth_version"] = "1.0" #,
    params["oauth_nonce"] = oauth.generate_nonce() #,
    params["oauth_timestamp"] = int(time.time())
    consumer = oauth.Consumer(key=key,
                              secret=secret)
    params["oauth_consumer_key"] = consumer.key
    req = oauth.Request(method=method, url=url, parameters=params)
    req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, None)

    req['q'] = req['q'].encode('utf8')
    req_url = req.to_url().replace('+', '%20')
    print req_url
    result = urllib2.urlopen(req_url)

    return result


if __name__ == "__main__":
    url = "http://yboss.yahooapis.com/ysearch/web"

    req = oauth_request(url, params={"q": "cats dogs"})
    # This one is a bit nasty. Apparently the BOSS API does not like
    # "+" in its URLs so you have to replace "%20" manually.
    # Not sure if the API should be expected to accept either.
    # Not sure why to_url does not just return %20 instead...
    # Also, oauth2.Request seems to store parameters as unicode and forget
    # to encode to utf8 prior to percentage encoding them in its to_url
    # method. However, it's handled correctly for generating signatures.
    # to_url fails when query parameters contain non-ASCII characters. To
    # work around, manually utf8 encode the request parameters.
    req['q'] = req['q'].encode('utf8')
    req_url = req.to_url().replace('+', '%20')
    print req_url
    result = urllib2.urlopen(req_url)


from husky.textutil import TextUtil


class YahooAPI(object):
    BASE_URL = "https://yboss.yahooapis.com/ysearch/web?"

    def __init__(self, key, secret):
        if key is None or secret is None:
            raise ValueError("API key cannot be None")
        self.key = key
        self.secret = secret
        self.config = None
        self.text_util = TextUtil()

    @staticmethod
    def from_config(api_config):
        api = YahooAPI(key=api_config["consumer_key"], secret=api_config["consumer_secret"])
        return api

    def make_query(self,
                     query_string=None,
                     count=50,
                     lang="en",
                     src="news"
                     ):
        q = {
            "q"             : query_string,
            "format"        : "json",
            "length"        : count,
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
                     query_size_heuristic=10):

        found_results = []
        total_results = None

        query_size = self.text_util.words_count(query["q"])

        for start_index in self.make_query_pages(max_results):

            if total_results is not None and start_index > total_results:
                break

            query["start"] = start_index

            try:
                api_response = oauth_request(self.BASE_URL, query, self.key, self.secret)
                print api_response
            except Exception:
                logging.error("Error while calling '%s':%s" % (query,  traceback.format_exc()))
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

        return found_results, [], 0 if total_results is None else total_results

    def __repr__(self):
        return "<FarooAPI(key='%s')>" % self.key[:8] + ".."
