# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import lxml
import nltk
import ftfy
import string
import langid
import difflib
import logging
import newspaper
import readability
import textblob.tokenizers

from lxml.etree import ParserError
from readability.readability import Unparseable

from husky.markup import Markup
from husky.markup import MarkupChunk
from husky.markup import EntityReference


class TextUtil(object):
    """
    TODO
    """
    RE_MULTIPLE_SPACE = re.compile(u"\s+", re.UNICODE)
    RE_WHITESPACE = re.compile(u" +", re.UNICODE)
    RE_EMPTY_STR = re.compile(u"^\s*$", re.UNICODE)
    RE_HTML_SPECIAL_CHARS = re.compile(u"&#?[a-z0-9]+;", re.UNICODE)
    RE_QUOTED_PHRASE = re.compile(u"\"([^\"]*)\"", re.UNICODE)
    RE_L_SPACE = re.compile(u"^\s+", re.UNICODE)
    RE_R_SPACE = re.compile(u"\s+$", re.UNICODE)
    RE_LQ = re.compile(u"^\s*\"\s*", re.UNICODE)
    RE_RQ = re.compile(u"\s*\"\s*$", re.UNICODE)

    def __init__(self):
        self.np_config = newspaper.configuration.Configuration()
        self.np_config.fetch_images = False
        self.seq_matcher = difflib.SequenceMatcher(None)

    def simplified_text(self, text, remove_punct=True):
        if text is None:
            return None
        text = text.lower()
        if isinstance(text, unicode):
            text = text.encode("utf-8")
        if remove_punct:
            text = text.translate(None, string.punctuation)
        text = self.RE_MULTIPLE_SPACE.sub(" ", text)
        text = " ".join(nltk.word_tokenize(text))
        return text

    def get_pretty_markup(self, html):
        clean_html = document = readability.Document(html).summary()
        paragraphs = lxml.html.fromstring(clean_html).xpath("//p")
        return [p.text_content() for p in paragraphs]

    def extract_body(self, url, html):

        try:
            document = readability.Document(html)
            summary = document.summary()
            lang_id, _ = langid.classify(summary)
            try:
                doc_title = document.title()
            except TypeError:
                doc_title = None
        except ParserError:
            lang_id = "en"
            document = None
            summary = ""
            doc_title = None
        except Unparseable:
            lang_id = "en"
            document = None
            summary = ""
            doc_title = None

        try:
            article = newspaper.Article(url, language=lang_id, config=self.np_config)
            article.set_html(html)
            article.parse()
        except IOError:
            # If language is not found, try to use English parser.
            article = newspaper.Article(url, language="en", config=self.np_config)
            article.set_html(html)
            article.parse()

        a_text = "" if article.text is None or len(article.text) == 0 else article.text
        r_text = "" if summary is None or len(summary) == 0 else summary
        r_text = nltk.clean_html(r_text)

        if len(a_text) > len(r_text):
            text = a_text
        else:
            text = r_text

        a_title = "" if article.title is None or len(article.title) == 0 else article.title
        r_title = "" if doc_title is None or len(doc_title) == 0 else doc_title

        if len(r_title) == 0:
            title = a_title
        else:
            title = r_title

        if len(title) > 0:
            title = self.norm_sentence(title)
            if title[-1] not in string.punctuation:
                title += "."

            text = title + "\n" + text

        text = text.replace(".\n", " ")

        try:
            text = ftfy.fix_text(text,
                                 fix_entities=True,
                                 remove_terminal_escapes=True,
                                 uncurl_quotes=True,
                                 fix_line_breaks=True)
        except UnicodeError:
            logging.error("Error while parsing HTML from %r" % url)
            return "", "en"

        return text, lang_id

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

    def words_count(self, sentence):
        if isinstance(sentence, unicode):
            sentence = sentence.encode("utf-8")
        no_punct = sentence.translate(None, string.punctuation)
        tokens = nltk.word_tokenize(no_punct)
        return len(tokens)

    def select_segments(self, sentences, quoted, min_length=10, min_size=5):

        sentences = map(self.remove_lr_quotes, map(self.norm_sentence, sentences))
        quoted = map(self.remove_lr_quotes, map(self.norm_sentence, quoted))
        segments = set()

        for segm in sentences + quoted:

            if len(segm) < min_length:
                continue

            if segm in segments:
                continue

            if self.words_count(segm) < min_size:
                continue

            segments.add(segm.replace("\"", ""))

        return list(segments)

    def compile_fuzzy_patterns(self, queries):
        patterns = {}
        for query_text in queries:
            query_re = self.compile_fuzzy_pattern(query_text)
            patterns[query_text] = query_re
        return patterns

    def compile_fuzzy_pattern(self, query_text):
        query_tokens = query_text.split(" ")
        query_re_tokens = ["(?:%s)?" % re.escape(query_tokens[0])]
        for i in xrange(1, len(query_tokens)):
            re_token = "(?: %s)?" % re.escape(query_tokens[i])
            query_re_tokens.append(re_token)
        query_re = "(%s)" % ".*?".join(query_re_tokens)
        query_re = re.compile(query_re, re.UNICODE | re.IGNORECASE)
        return query_re

    def ffs(self, text, query_text, fuzzy_pattern, min_threshold=0.5, max_threshold=1.5, min_m_size=5, min_ratio=0.5):

        if query_text in text:
            return True

        min_len = max(len(query_text) * min_threshold, min_m_size)
        max_len = len(query_text) * max_threshold

        matches = [m for m in fuzzy_pattern.findall(text) if min_len < len(m) < max_len]

        if len(matches) == 0:
            return False

        self.seq_matcher.set_seq1(query_text)

        for m in matches:

            self.seq_matcher.set_seq2(m)
            ratio = self.seq_matcher.ratio()

            if ratio > min_ratio:
                return True

        return False

    def fuzzy_search(self, text, query_text, fuzzy_pattern, min_threshold=0.5, max_threshold=1.5, min_m_size=5):

        min_len = max(len(query_text) * min_threshold, min_m_size)
        max_len = len(query_text) * max_threshold
        
        mm = fuzzy_pattern.findall(text)
        matches = [m for m in mm if min_len < len(m) < max_len]

        if len(matches) == 0:
            return 0.0, None

        best_ratio = 0.0
        best_match = None

        self.seq_matcher.set_seq1(query_text)

        for m in matches:

            self.seq_matcher.set_seq2(m)
            ratio = self.seq_matcher.ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = m

        return best_ratio, best_match


    def fuzzy_group_search(self, text, query_text, fuzzy_pattern, min_threshold=0.5, max_threshold=1.5, min_m_size=5):

        min_len = max(len(query_text) * min_threshold, min_m_size)
        max_len = len(query_text) * max_threshold

        match_groups = [m for m in fuzzy_pattern.finditer(text)]
        matches = []

        for m_g in match_groups:
            if min_len < len(m_g.group()) < max_len:
                matches.append(m_g)

        if len(match_groups) == 0:
            return 0.0, None

        best_ratio = 0.0
        best_match = None

        self.seq_matcher.set_seq1(query_text)

        for m in matches:

            self.seq_matcher.set_seq2(m.group())
            ratio = self.seq_matcher.ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = m

        return best_ratio, best_match


    def generate_markup(self, title, text, paragraphs, bodies, trim=32, min_ratio=0.00):

        paragraphs = [title] + paragraphs

        markup = Markup.blank()

        for i, paragraph in enumerate(paragraphs):

            paragraph_markup = MarkupChunk(text=paragraph)
            if i == 0:
                markup.set_title(paragraph_markup)
            else:
                markup.add_body_element(paragraph_markup)

            sentences = self.sent_tokenize(paragraph)
            quotes = self.extract_quoted(paragraph)
            segments = self.select_segments(sentences, quotes, min_size=5)
            segments = [self.simplified_text(s) for s in segments]

            if trim is not None and trim > 0:
                for i in xrange(len(segments)):
                    segments[i] = " ".join(segments[i].split()[:trim])

            triggered_regexes = []

            for segment in segments:
                fuzzy_pattern = self.compile_fuzzy_pattern(segment)
                found_refs = []
                for body, body_id in bodies:
                    if self.ffs(body, segment, fuzzy_pattern, min_ratio=0.3):
                        found_refs.append(body_id)
                if len(found_refs) > 0:
                    triggered_regexes.append((segment, fuzzy_pattern, found_refs))

            for segment, fuzzy_pattern, found_refs in triggered_regexes:

                ratio, match = self.fuzzy_group_search(paragraph,
                                                       segment,
                                                       fuzzy_pattern,
                                                       min_threshold=0,
                                                       max_threshold=10)

                if ratio >= min_ratio:

                    ref_object = EntityReference(span=match.span(),
                                                 match=match.group(),
                                                 references=found_refs,
                                                 extra_attr={"ratio": ratio})
                    paragraph_markup.add_ref(ref_object)


        return markup