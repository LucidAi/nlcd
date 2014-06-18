# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import nltk
import langid
import newspaper
import readability
import textblob.tokenizers


class SimpleArticle(object):

    def __init__(self, url, title, text, lang_id):
        self.url = url
        self.title = title
        self.text = text
        self.lang_id = lang_id


class TextMiner(object):

    RE_WHITESPACE = re.compile(" +")
    RE_EMPTY_STR = re.compile("^\s*$")
    RE_HTML_SPECIAL_CHARS = re.compile("\&#?[a-z0-9]+;")

    RE_QUOTES = re.compile(u"\"“”", re.UNICODE)

    RE_Q_PHRASE_PATTERN_1 = re.compile(u"\"([^\"]*)\"", re.UNICODE)
    RE_Q_PHRASE_PATTERN_2 = re.compile(u"\'([^\']*)\'", re.UNICODE)
    RE_Q_PHRASE_PATTERN_3 = re.compile(u"“([^”]*)”", re.UNICODE)

    @staticmethod
    def extract_article(url, html):
        document = readability.Document(html)
        summary = document.summary()
        lang_id, _ = langid.classify(summary)
        article = newspaper.Article(url, language=lang_id)
        article.set_html(html)
        article.parse()
        if len(article.text) == 0:
            text = nltk.clean_html(document.summary()).replace("\n", " ")
        else:
            text = article.text
        return SimpleArticle(url,
                             article.title,
                             text,
                             lang_id)

    def clean_html_junk(self, text):
        return self.RE_HTML_SPECIAL_CHARS.sub("", text)

    def sent_tokenize(self, text):
        text = text.decode("utf-8")
        text = self.clean_html_junk(text)
        lines = text.split("\n")
        sentences = []
        for line in lines:
            sentences.extend(textblob.tokenizers.sent_tokenize(line))
        sentences = [sent for sent in sentences if not self.RE_EMPTY_STR.match(sent)]
        return [self.RE_WHITESPACE.sub(" ", sent) for sent in sentences]

    def extract_quoted(self, sentence_list):
        quoted = []
        for sent in sentence_list:
            quoted.extend(self.RE_Q_PHRASE_PATTERN_1.findall(sent))
            # quoted.extend(self.RE_Q_PHRASE_PATTERN_2.findall(sent))
            quoted.extend(self.RE_Q_PHRASE_PATTERN_3.findall(sent))
        return quoted
