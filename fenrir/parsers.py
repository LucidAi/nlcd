# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu> (2014)


class ArticleParser(object):
    """
    TODO(zaytsev@usc.edu):
    """

    SELECTOR = "descendant-or-self::*"
    NAMESPACE = {"re": "http://exslt.org/regular-expressions"}

    NO_CONTENT = ""
    TAG_META = "meta"
    TAG_META_CONTENT = "@content"

    def get_content(self, element):
        content = self.NO_CONTENT

        if element.tag == self.TAG_META:
            mm = element.xpath(self.TAG_META_CONTENT)
            if len(mm) > 0:
                content = mm[0]
        else:
            content = element.text or self.NO_CONTENT

        return content

    def get_by_attr(self, node, attr, value):
        selector = "%s[re:test(@%s, \"%s\", \"i\")]" % (self.SELECTOR, attr, value)
        found_elements = node.xpath(selector, namespaces=self.NAMESPACE)
        return found_elements