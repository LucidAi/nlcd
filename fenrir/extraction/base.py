# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import langid
import newspaper
import textblob.tokenizers

from nltk.corpus import stopwords
from fenrir.extraction import NLCD_TO_NLTK_LANG


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

    RE_Q_PHRASE_PATTERN_1 = re.compile("\"([^\"]*)\"")
    RE_Q_PHRASE_PATTERN_2 = re.compile("\'([^\']*)\'")
    RE_Q_PHRASE_PATTERN_3 = re.compile("“([^“”]*)”")

    def __init__(self):
        pass

    @staticmethod
    def extract_article(url, html):
        article = newspaper.Article(url)
        article.set_html(html)
        article.parse()
        lang_id, _ = langid.classify(article.title)
        article = newspaper.Article(url, language=lang_id)
        article.set_html(html)
        article.parse()
        return SimpleArticle(url,
                             article.title,
                             article.text,
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
            quoted.extend(self.RE_Q_PHRASE_PATTERN_2.findall(sent))
            quoted.extend(self.RE_Q_PHRASE_PATTERN_3.findall(sent))
        return quoted

    def filter_sents(self, sentence_list, langid,
                           keywords=set(),
                           tokens_min=7,
                           tokens_max=40,
                           min_nonstop=5,
                           min_keywords=1,
                           or_min_ner=2,
                           min_rakewords=5):

        filtered = []
        sentence_list = list(set((s for s in sentence_list if len(s) > 0)))
        stoplist = set(stopwords.words(NLCD_TO_NLTK_LANG[langid]))
        self.rake.stopwords = stoplist


        rake_keywords = set(self.rake.extract(sentence_list))
        # entities = self.ner.extract_entities(sentence_list)

        for sentno, sent in enumerate(sentence_list):
            text = sent.decode("utf-8")
            is_key_sent = True

            tokens = [t.lower() for t in textblob.TextBlob(text).tokens]
            triggers = []


            n_tokens = 0
            for t in tokens:
                if len(t) >= 3:
                    n_tokens += 1

            #
            if n_tokens < tokens_min or n_tokens > tokens_max:
                is_key_sent = False
                triggers.append("N_TOKENS")

            #
            n_keywords = 0 if len(keywords) > 0 else min_keywords
            for t in tokens:
                if t in keywords:
                    n_keywords += 1
            if n_keywords < min_keywords:
                # is_key_sent = F
                triggers.append("N_KEYWORDS")

            #
            n_nonstop = 0
            for t in tokens:
                if t not in stoplist:
                    n_nonstop += 1
            if n_nonstop < min_nonstop:
                is_key_sent = False
                triggers.append("N_NONSTOP")


            n_rakewords = 0
            rakewords = []
            for r in rake_keywords:
                if r in sent:
                    n_rakewords += 1
                    rakewords.append(r)
            if n_rakewords < min_rakewords:
                is_key_sent = False
                triggers.append("N_RAKEWORD")

            #
            # if langid == "en":
                # entities = []
                # entities = self.ner.extract_entities([sent], False, "E")
                # if len(entities) >= or_min_ner:
                #     is_key_sent = True


            filtered.append((is_key_sent, {
                "text": sent,
                "nTokens": n_tokens,
                "nNonstop": n_nonstop,
                "nKeywords": n_keywords,
                "nRakewords": n_rakewords,
                # "namedEntities": [e["entity"] for e in entities],
                "rakeWords": rakewords,
                "triggers": triggers,
            }))

        return filtered

