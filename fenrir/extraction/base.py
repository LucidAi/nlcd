# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import textblob


class TextPreprocessor(object):

    HTML_SPECIAL_CHARS = re.compile("\&#?[a-z0-9]+;")

    def __init__(self):
        pass

    def clean_html_junk(self, text):
        return self.HTML_SPECIAL_CHARS.sub("", text)

    def sent_segmentize(self, text):
        text = self.clean_html_junk(text)
        lines = text.split("\n")
        sents = []
        for line in lines:
            blob = textblob.TextBlob(line)
            sents.extend(map(str, blob.sentences))
        return sents

