# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import newspaper

from fenrir.extraction.article import Annotation
from fenrir.extraction.article import IAnnotator


class HtmlAnnotationsExtractor(IAnnotator):
    """Class which extracts annotations from HTML markup."""

    def annotate(self, item):
        url, html = item
        np_article = newspaper.Article(url)
        np_article.set_html(html)
        np_article.parse()
        return Annotation(np_article, annotator=self)

    def extract_images(self, data):
        return [data.top_image]

    def extract_sources(self, data):
        return []

    def extract_title(self, data):
        return []

    def extract_authors(self, data):
        authors = data.authors
        return authors

    def extract_url(self, data):
        return ""

    def extract_dates(self, data):
        return []

    def __init__(self):
        pass