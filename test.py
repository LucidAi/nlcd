#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import unittest


from fenrir.fetcher import Fetcher
from fenrir.app import FenrirWorker


TEST_URLS = open("tests/links.txt").read().rstrip().split("\n")


class FetcherTestCase(unittest.TestCase):

    def test_recreate(self):
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

class FenrirWorkerTestCase(unittest.TestCase):

    def __init__(self):
        pass


if __name__ == "__main__":
    unittest.main()