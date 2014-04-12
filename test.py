#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import json
import unittest


from fenrir.app import FenrirWorker
from fenrir.fetcher import Fetcher
from fenrir.api import CseAPI


TEST_URLS = open("tests/eng/links.txt").read().rstrip().split("\n")
TEST_QUERIS = open("tests/eng/queries.txt").read().rstrip().split("\n")
TEST_RJSONS = json.loads(open("tests/eng/google_jsons.json", "rb").read())

class CseAPITestCase(unittest.TestCase):

    def test_init(self):
        with open("fab/tests.json", "rb") as fl:
            configs = json.load(fl)
        api = (api for api in configs["api"] if api["id"] == "google.CseAPI").next()
        cse = CseAPI(key=api["google_api_key"], engine_id=api["google_engine_id"])
        self.assertEqual(cse.key, api["google_api_key"])
        self.assertEqual(cse.engine_id, api["google_engine_id"])

    # def test_search(self):
    #     with open("fab/tests.json", "rb") as fl:
    #         configs = json.load(fl)
    #     api = (api for api in configs["api"] if api["id"] == "google.CseAPI").next()
    #     cse = CseAPI(key=api["google_api_key"], engine_id=api["google_engine_id"])
    #     for query_string in TEST_QUERIS:
    #         self.assertIsNotNone(cse.search(query_string))



# class FetcherTestCase(unittest.TestCase):

#     def test_init(self):
#         fetcher = Fetcher()

#     def test_fetch(self):
#         fetcher = Fetcher()
#         for url in TEST_URLS:
#             html = fetcher.fetch(url).replace("\n", "").replace("\t", "").replace(" ", "")
#             self.assertTrue(html.startswith("<!DOCTYPE"))

#     def test_fetch_document(self):
#         fetcher = Fetcher()
#         for url in TEST_URLS:
#             doc = fetcher.fetch_document(url)
#             self.assertIsNotNone(doc)

#     def serch(self, text_query):
#         pass

# class FenrirWorkerTestCase(unittest.TestCase):

#     def __init__(self):
#         pass


if __name__ == "__main__":
    unittest.main()