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

    def test_make_query(self):
        with open("fab/tests.json", "rb") as fl:
            configs = json.load(fl)
        api = (api for api in configs["api"] if api["id"] == "google.CseAPI").next()
        cse = CseAPI(key=api["google_api_key"], engine_id=api["google_engine_id"])
        for query_string in TEST_QUERIS:
            self.assertIsNotNone(cse.make_query(query_string=query_string))

    def test_query_indexes(self):
        with open("fab/tests.json", "rb") as fl:
            configs = json.load(fl)
        api = (api for api in configs["api"] if api["id"] == "google.CseAPI").next()
        cse = CseAPI(key=api["google_api_key"], engine_id=api["google_engine_id"])
        nums = [(1, [1]),
                (11, [1, 11]),
                (10, [1]),
                (22, [1, 11, 21]),
                (100, [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]),
                (21, [1, 11, 21]),
                (0, []),
        ]
        for num, true_start_indeces in nums:
            start_indeces = list(cse.make_query_pages(num))
            self.assertEqual(start_indeces, true_start_indeces)

    # def test_find_results(self):
    #     with open("fab/tests.json", "rb") as fl:
    #         configs = json.load(fl)
    #     api = (api for api in configs["api"] if api["id"] == "google.CseAPI").next()
    #     cse = CseAPI(key=api["google_api_key"], engine_id=api["google_engine_id"])
    #     all_results = []
    #     for query_string in TEST_QUERIS:
    #         query = cse.make_query(query_string=query_string)
    #         results = cse.find_results(query, number=100)
    #         all_results.append({
    #             "query_string": query_string,
    #             "result_items": list(results)
    #         })
    #     with open("tests/eng/resul_items.json", "wb") as fl:
    #         json.dump(all_results, fl)



class FetcherTestCase(unittest.TestCase):

    def test_init(self):
        fetcher = Fetcher()

    def test_fetch(self):
        fetcher = Fetcher()
        for url in TEST_URLS:
            html = fetcher.fetch(url).replace("\n", "").replace("\t", "").replace(" ", "")
            self.assertTrue(html.startswith("<!DOCTYPE"))

    def test_fetch_document(self):
        fetcher = Fetcher()
        for url in TEST_URLS:
            doc = fetcher.fetch_document(url)
            self.assertIsNotNone(doc)

# class FenrirWorkerTestCase(unittest.TestCase):

#     def __init__(self):
#         pass


if __name__ == "__main__":
    unittest.main()