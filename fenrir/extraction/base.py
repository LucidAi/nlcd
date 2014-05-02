# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import nltk
import langid
import textblob
import newspaper
import readability

from client.api import common


class TextPreprocessor(object):

    RE_WHITESPACE = re.compile(" +")
    RE_EMPTY_STR = re.compile("^\s*$")
    RE_HTML_SPECIAL_CHARS = re.compile("\&#?[a-z0-9]+;")

    RE_Q_PHRASE_PATTERN_1 = re.compile("\"([^\"]*)\"")
    RE_Q_PHRASE_PATTERN_2 = re.compile("\'([^\"]*)\'")
    RE_Q_PHRASE_PATTERN_3 = re.compile("“([^“”]*)”")

    def __init__(self):
        pass

    def extract_article(self, url, html):
        lang, _ = self.html_langid(html)
        article = newspaper.Article(url, language=lang)
        article.set_html(html)
        article.parse()
        article.nlp()
        return article

    def html_to_text(self, html):
        doc = readability.Document(html)
        summary = doc.summary()
        text = nltk.util.clean_html(summary)
        return text

    def html_langid(self, html):
        return langid.classify(self.html_to_text(html))

    def langid(self, text):
        return langid.classify(text)

    def clean_html_junk(self, text):
        return self.RE_HTML_SPECIAL_CHARS.sub("", text)

    def sent_segmentize(self, text):
        text = self.clean_html_junk(text)
        lines = text.split("\n")
        sents = []
        for line in lines:
            blob = textblob.TextBlob(line)
            sents.extend(map(str, blob.sentences))
        sents = [sent for sent in sents if not self.RE_EMPTY_STR.match(sent)]
        return [self.RE_WHITESPACE.sub(" ", sent) for sent in sents]

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
        sentence_list = list(set((s for s in sentence_list if len(s) > 0)))
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

