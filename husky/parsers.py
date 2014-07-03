# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu> (2014)

import lxml.html
from lxml.html.clean import Cleaner


class ArticleParser(object):
    """
    TODO(zaytsev@usc.edu):
    """

    SELECTOR = "descendant-or-self::*"
    SELECTOR_PATTERN = "%s[re:test(@%s, \"%s\", \"i\")]"
    NAMESPACE = {"re": "http://exslt.org/regular-expressions"}

    NO_CONTENT = ""
    TAG_META = "meta"
    TAG_META_CONTENT = "@content"

    def __init__(self):
        self.cleaner = Cleaner()
        self.cleaner.javascript = True
        self.cleaner.comments = True
        self.cleaner.style = True

    def blacklist_elements(self, elements, blacklist):
        for elem in elements:
            if "class" in elem.attrib and elem.attrib["class"] in blacklist:
                continue
            yield elem

    def get_clean_document(self, article):
        doc = article.clean_doc
        doc = self.cleaner.clean_html(doc)
        html = lxml.html.tostring(doc, pretty_print=True)
        doc = lxml.html.fromstring(html)
        return html, doc

    def get_content(self, element):
        content = self.NO_CONTENT

        if element.tag == self.TAG_META:
            mm = element.xpath(self.TAG_META_CONTENT)
            if len(mm) > 0:
                content = [mm[0]]
        else:
            content = element.xpath(".//text()")

        return content

    def get_by_attr(self, node, attr, value):
        selector = self.SELECTOR_PATTERN % (self.SELECTOR, attr, value)
        found_elements = node.xpath(selector, namespaces=self.NAMESPACE)
        return found_elements