# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import textblob

from client.api import common


class TextPreprocessor(object):

    RE_HTML_SPECIAL_CHARS = re.compile("\&#?[a-z0-9]+;")

    RE_Q_PHRASE_PATTERN_1 = re.compile("\"([^\"]*)\"")
    RE_Q_PHRASE_PATTERN_2 = re.compile("\'([^\"]*)\'")
    RE_Q_PHRASE_PATTERN_3 = re.compile("“([^“”]*)”")

    def __init__(self):
        pass

    def clean_html_junk(self, text):
        return self.RE_HTML_SPECIAL_CHARS.sub("", text)

    def sent_segmentize(self, text):
        text = self.clean_html_junk(text)
        lines = text.split("\n")
        sents = []
        for line in lines:
            blob = textblob.TextBlob(line)
            sents.extend(map(str, blob.sentences))
        return sents

    def extract_quoted(self, sentence_list):
        quoted = []
        for sent in sentence_list:
            quoted.extend(self.RE_Q_PHRASE_PATTERN_1.findall(sent))
            quoted.extend(self.RE_Q_PHRASE_PATTERN_2.findall(sent))
            quoted.extend(self.RE_Q_PHRASE_PATTERN_3.findall(sent))
        return quoted

    def filter_sents(self, sentence_list,
                           tokens_min=4,
                           tokens_max=30):
        filtered = []
        for sentno, sent in enumerate(sentence_list):
            text = sent.decode("utf-8")
            tokens = [t.lower() for t in textblob.TextBlob(text).tokens]
            tk_size = len(tokens)
            tx_size = len(text)
            is_important = tk_size >= tokens_min and tk_size <= tokens_max
            filtered.append({
                "id": sentno,
                "text": text,
                "tokens": tokens,
                "tk_size": tk_size,
                "tx_size": tx_size,
                "is_important": is_important
            })
        return filtered

