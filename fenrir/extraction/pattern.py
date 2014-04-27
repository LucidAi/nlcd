# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import jsonpath_rw


def get_extractor(api_name):
    return EXTRACTORS[api_name]()


class CseFieldExtractor(object):
    """
    """

    JPATH_EXPRESSIONS_SITE = [
        jsonpath_rw.parse("pagemap.NewsItem[*].site_name"),
        jsonpath_rw.parse("pagemap.metatags[*].['og:site_name']"),
        jsonpath_rw.parse("pagemap.metatags[*].['source']"),
        jsonpath_rw.parse("pagemap.metatags[*].['twitter:site']"),
        jsonpath_rw.parse("pagemap.metatags[*].['article:publisher']"),
        jsonpath_rw.parse("pagemap.metatags[*].['article:publisher']"),
        jsonpath_rw.parse("displayLink"),
    ]

    JPATH_EXPRESSIONS_AUTHOR = [
        jsonpath_rw.parse("pagemap.person[*].name"),
        jsonpath_rw.parse("pagemap.hcard[*].fn"),
        jsonpath_rw.parse("pagemap.article[*].author"),
        jsonpath_rw.parse("pagemap.metatags[*].author"),
        jsonpath_rw.parse("pagemap.metatags[*].['dc.creator']"),
        jsonpath_rw.parse("pagemap.metatags[*].['twitter:creator']"),
        jsonpath_rw.parse("pagemap.metatags[*].['sailthru.author']"),
    ]

    JPATH_EXPRESSIONS_DATES = [
        jsonpath_rw.parse("pagemap.NewsItem[*].datePublished"),
        jsonpath_rw.parse("pagemap.article[*].datePublished"),
        jsonpath_rw.parse("pagemap.metatags[*].['dc.date.issued']"),
    ]

    JPATH_EXPRESSIONS_TITLES = [
        jsonpath_rw.parse("title"),
        jsonpath_rw.parse("htmlTitle"),
        jsonpath_rw.parse("pagemap.NewsItem[*].title"),
        jsonpath_rw.parse("htmlTitle"),
        jsonpath_rw.parse("pagemap.metatags[*].['og:title']"),
    ]

    def extract_authors(self, found_document):
        authors = set()
        for matcher in self.JPATH_EXPRESSIONS_AUTHOR:
            authors.update([m.value for m in matcher.find(found_document)])
        return list(authors)

    def extract_sources(self, found_document):
        sources = set()
        for matcher in self.JPATH_EXPRESSIONS_SITE:
            sources.update([m.value for m in matcher.find(found_document)])
        return list(sources)

    def extract_urls(self, found_document):
        return [found_document.get("formattedUrl")]

    def extract_titles(self, found_document):
        titles = set()
        for matcher in self.JPATH_EXPRESSIONS_TITLES:
            titles.update([m.value for m in matcher.find(found_document)])
        return list(titles)

    def extract_publish_dates(self, found_document):
        dates = set()
        for matcher in self.JPATH_EXPRESSIONS_DATES:
            dates.update([m.value for m in matcher.find(found_document)])
        return list(dates)

#
EXTRACTORS = {

    "api.GoogleCSE": CseFieldExtractor,

}
