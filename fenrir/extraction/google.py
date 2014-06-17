# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import json
import nltk

from fenrir.extraction.article import Annotation
from fenrir.extraction.article import IAnnotator
from fenrir.extraction.pattern import JsonPatternMatchingUtil


class CseAnnotationExtractor(IAnnotator):
    """
    Annotations extractor for google CSE result items.
    """
    DEFAULT_CONFIGURATION_PATH = "./distr/patterns/google.cse.json"

    def __init__(self):
        with open(self.DEFAULT_CONFIGURATION_PATH, "rb") as i_fl:
            self.patterns = json.load(i_fl)

        self.util = JsonPatternMatchingUtil()
        self.url_pattern = self.util.compile(self.patterns, "url")
        self.title_pattern = self.util.compile(self.patterns, "title")
        self.authors_pattern = self.util.compile(self.patterns, "authors")
        self.sources_pattern = self.util.compile(self.patterns, "sources")
        self.dates_pattern = self.util.compile(self.patterns, "dates")
        self.images_pattern = self.util.compile(self.patterns, "images")
        self.snippet_pattern = self.util.compile(self.patterns, "snippet")

    def annotate(self, item):
        return Annotation(item, annotator=self)

    def extract_url(self, item):
        return self.util.match_first(self.url_pattern, item)

    def extract_title(self, item):
        titles = self.util.match(self.title_pattern, item)
        titles = list(set([nltk.clean_html(t) for t in titles]))
        titles.sort(key=lambda title: len(title))
        return titles

    def extract_authors(self, item):
        return self.util.match_unique(self.authors_pattern, item)

    def extract_sources(self, item):
        return self.util.match_unique(self.sources_pattern, item)

    def extract_dates(self, item):
        dates = self.util.match(self.dates_pattern, item)
        s_date = self.util.match_first(self.snippet_pattern, item)[:12].rstrip()
        dates.append(s_date)
        return list(set(dates))

    def extract_images(self, item):
        return self.util.match_unique(self.images_pattern, item)

    def __repr__(self):
        return "<CseAnnotationExtractor()>"