# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import ftfy
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

    RE_WHITESPACE = re.compile(u" +", re.UNICODE)
    RE_EMPTY_STR = re.compile(u"^\s*$", re.UNICODE)
    RE_HTML_SPECIAL_CHARS = re.compile(u"&#?[a-z0-9]+;", re.UNICODE)
    RE_QUOTED_PHRASE = re.compile(u"\"([^\"]*)\"", re.UNICODE)

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
        text = ftfy.fix_text(text,
                             fix_entities=True,
                             remove_terminal_escapes=True,
                             uncurl_quotes=True,
                             fix_line_breaks=True)
        return SimpleArticle(url,
                             article.title,
                             text,
                             lang_id)

    def sent_tokenize(self, text):
        lines = text.split("\n")
        sentences = []
        for line in lines:
            sentences.extend(textblob.tokenizers.sent_tokenize(line))
        sentences = [sent for sent in sentences if not self.RE_EMPTY_STR.match(sent)]
        return [self.RE_WHITESPACE.sub(" ", sent) for sent in sentences]

    def extract_quoted(self, text):
        return self.RE_QUOTED_PHRASE.findall(text)
