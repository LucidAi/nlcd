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
    RE_L_SPACE = re.compile(u"^\s+", re.UNICODE)
    RE_R_SPACE = re.compile(u"\s+$", re.UNICODE)
    RE_LQ = re.compile(u"^\s*\"\s*", re.UNICODE)
    RE_RQ = re.compile(u"\s*\"\s*$", re.UNICODE)

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

    def norm_sentence(self, sentence):
        sentence = self.RE_L_SPACE.sub("", sentence)
        sentence = self.RE_R_SPACE.sub("", sentence)
        return sentence

    def remove_lr_quotes(self, sentence):
        sentence = self.RE_LQ.sub("", sentence)
        sentence = self.RE_RQ.sub("", sentence)
        return sentence

    def combine_sentences(self, sentences, quoted, min_length=10):
        sentences = map(self.remove_lr_quotes, map(self.norm_sentence, sentences))
        quoted = map(self.remove_lr_quotes, map(self.norm_sentence, quoted))
        all_sentences = set((s for s in quoted if len(s) >= min_length))
        for sentence in sentences:
            if len(sentence) < min_length:
                continue
            if sentence in all_sentences:
                continue
            all_sentences.add(sentence.replace("\"", ""))
        return list(all_sentences)
