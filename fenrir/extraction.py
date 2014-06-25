# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import abc
import json
import logging
import datetime

import ner
import nltk
import ftfy
import langid
import newspaper
import jsonpath_rw
import readability
import parsedatetime
import textblob.tokenizers

from fenrir.entity import Entity
from fenrir.parsers import ArticleParser


NLCD2NLTK_LANG = {
    "en": "english",
    "ru": "russian",
    "de": "german",
    "it": "italian",
}

NLTK2NLCD_LANG = {
    nltk: nlcd for nlcd, nltk
    in NLCD2NLTK_LANG.iteritems()
}


class IAnnotator(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def annotate(self, data, *args, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def extract_url(self, item, *args, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def extract_title(self, item, *args, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def extract_authors(self, data, *args, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def extract_sources(self, data, *args, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def extract_dates(self, data, *args, **kwargs):
        raise NotImplemented()

    @abc.abstractmethod
    def extract_images(self, data, *args, **kwargs):
        raise NotImplemented()


class Annotation(object):
    """Class for accessing articles annotation data.
    """

    def __init__(self, data, annotator=None):
        self.data = data

        self.url = None
        self.title = None
        self.authors = None
        self.sources = None
        self.dates = None
        self.images = []

        self.ref_links = []
        self.ref_people = []
        self.ref_orgs = []
        self.ref_authors = []
        self.ref_sources = []

        if annotator is not None:
            self.url = annotator.extract_url(self.data)
            self.title = annotator.extract_title(self.data)
            self.authors = annotator.extract_authors(self.data)
            self.sources = annotator.extract_sources(self.data)
            self.dates = annotator.extract_dates(self.data)
            self.images = annotator.extract_images(self.data)

            self.ref_links = []
            self.ref_people = []
            self.ref_orgs = []
            self.ref_authors = []
            self.ref_sources = []


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


class NerExtractor(object):
    def __init__(self):
        # self.st = NERTagger("vendor/stanford-ner-models/english.all.3class.distsim.crf.ser.gz",
        # "vendor/stanford-ner/stanford-ner-2014-01-04.jar")
        self.st = ner.SocketNER(host="127.0.0.1", port=8000)


    def apply_truecase(self, tokens):
        tokens = tokens[:]
        for i in xrange(len(tokens)):
            if len(tokens[i]) <= 3 or tokens[i][0] == "@":
                continue
            elif tokens[i].isupper():
                tokens[i] = tokens[i].title()
        return tokens

    def extract_entities(self, texts, truecase=True, set_label=None):
        """Extracts named entites from set of strings.

        Args:
            texts (list): Collection of input strings.

        Kwargs:
            truecase (bool): If True, method applies heuristic to match true cases of words
                             in texts (improves quality on short strings).
            set_label (str): If not None, then method uses binary classification and label
                             found entities with provided label value. Otherwise uses
                             multiclass classification with default NLTK NE labels.

        Returns:
            (set): Set of pairs (entity, label).
        """
        entities = []

        for text in texts:
            sentences = nltk.sent_tokenize(text)
            # sentences = [nltk.word_tokenize(sent) for sent in sentences]
            # if truecase:
            # for i, sent in enumerate(sentences):
            #         sentences[i] = self.apply_truecase(sent)
            for sent in sentences:
                print sent
                tree = self.st.get_entities(sent)
                print tree
                print
                print
                prev_tag = None
        exit(0)
        # for w, tag in tree:
        # if tag is not "O":
        #         if tag != prev_tag:
        #             entities.append((tag, []))
        #         entities[-1][1].append(w)
        #     prev_tag = tag

        # ner_tree = nltk.ne_chunk(sent, binary=set_label is not None)
        # for ne in ner_tree:
        #     if hasattr(ne, "node"):
        #         entities.add((ne.node, " ".join(l[0] for l in ne.leaves())))
        # if set_label is not None:
        #     entities = [{"label":set_label, "entity": entity} for label,entity in entities]
        # else:
        #     entities = [{"label":label, "entity": entity} for label,entity in entities]

        if set_label is not None:
            entities = [{"label": set_label, "entity": " ".join(entity)} for label, entity in entities]
        else:
            entities = [{"label": label, "entity": " ".join(entity)} for label, entity in entities]

        print entities

        return entities


class CseAnnotationExtractor(IAnnotator):
    """
    Annotations extractor for google CSE result items.
    """
    DEFAULT_CONFIGURATION_PATH = "./distr/patterns/google.cse.json"

    def __init__(self):
        with open(self.DEFAULT_CONFIGURATION_PATH, "rb") as i_fl:
            self.patterns = json.load(i_fl)

        self.util = JsonPatternMatchingUtil()
        self.url_pattern = self.util.compile(self.patterns, "url")
        self.title_pattern = self.util.compile(self.patterns, "title")
        self.authors_pattern = self.util.compile(self.patterns, "authors")
        self.sources_pattern = self.util.compile(self.patterns, "sources")
        self.dates_pattern = self.util.compile(self.patterns, "dates")
        self.images_pattern = self.util.compile(self.patterns, "images")
        self.snippet_pattern = self.util.compile(self.patterns, "snippet")

    def annotate(self, item):
        return Annotation(item, annotator=self)

    def extract_url(self, item):
        return self.util.match_first(self.url_pattern, item)

    def extract_title(self, item):
        titles = self.util.match(self.title_pattern, item)
        titles = list(set([nltk.clean_html(t) for t in titles]))
        titles.sort(key=lambda title: len(title))
        return titles

    def extract_authors(self, item):
        return self.util.match_unique(self.authors_pattern, item)

    def extract_sources(self, item):
        return self.util.match_unique(self.sources_pattern, item)

    def extract_dates(self, item):
        dates = self.util.match(self.dates_pattern, item)
        s_date = self.util.match_first(self.snippet_pattern, item)[:12].rstrip()
        dates.append(s_date)
        return list(set(dates))

    def extract_images(self, item):
        return self.util.match_unique(self.images_pattern, item)

    def __repr__(self):
        return "<CseAnnotationExtractor()>"


class JsonPatternMatchingUtil(object):
    @staticmethod
    def compile(json_patterns, field_name):
        patterns = json_patterns[field_name]
        compiled = [jsonpath_rw.parse(pattern) for pattern in patterns]
        return compiled

    @staticmethod
    def match(compiled, json_dict):
        all_matches = []
        for matcher in compiled:
            for matched in matcher.find(json_dict):
                all_matches.append(matched.value)
        return all_matches

    @staticmethod
    def match_unique(compiled, json_dict):
        all_matches = set()
        for matcher in compiled:
            for matched in matcher.find(json_dict):
                all_matches.add(matched.value)
        return list(all_matches)

    @staticmethod
    def match_first(compiled, json_dict):
        for matcher in compiled:
            for matched in matcher.find(json_dict):
                return matched.value


class INormalizer(object):
    __metaclass__ = abc.ABCMeta
    EMPTY_RETURN = -1


class AuthorNormalizer(INormalizer):

    RE_NOTALLOWED = re.compile("\d|:|\|", re.UNICODE)
    RE_BYLINE = re.compile("by[\:\s\|]|from[\:\s]", re.UNICODE | re.IGNORECASE)
    RE_SEP = re.compile(u"[\r\n,;]|\Wand\W", re.UNICODE | re.IGNORECASE)
    RE_SPACE = re.compile(u"\s", re.UNICODE)
    RE_MULTIPLE_SPACES = re.compile(u"\s+", re.UNICODE)
    RE_BRACKETS = re.compile("\(.*?\)")
    RE_TWITTER = re.compile(u"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9]+)", re.UNICODE)

    MAX_INPUT_LEN = 120

    def __init__(self):
        pass

    def canonical(self, name_string, title=True):
        name_string.lstrip().rstrip()
        if title:
            return name_string.title()
        return name_string

    def classify_author_string(self, raw_entity, article=None):
        """
        Input is raw string possibly extracted from HTML and probably containing one or
        more author names, and sometimes sources.
        """
        if raw_entity.is_classified:
            return raw_entity
        if raw_entity.raw is None:
            logging.warn("Entity raw representation is None.")
            return []
        if len(raw_entity.raw) > self.MAX_INPUT_LEN:
            logging.warn("Too long string, probably some mistake '%s..'." % raw_entity.raw[:10])
            return []

        raw = raw_entity.raw
        candidates = set()
        entities = []

        # Remove "byline"
        raw = self.RE_BYLINE.sub("", raw)

        # Remove words in brackets
        raw = self.RE_BRACKETS.sub("", raw)

        # Split by separator symbol.
        raw_tokens = self.RE_SEP.split(raw)

        for raw_token in raw_tokens:

            # Clean token. Map multiple spaces into one space character.
            raw_token = self.RE_SPACE.sub(raw_token, " ")
            raw_token = self.RE_MULTIPLE_SPACES.sub(raw_token, " ").lstrip().rstrip()

            # Check if token has not-allowed symbols.
            if bool(self.RE_NOTALLOWED.search(raw_token)):
                # This is probably website user name or something else. We don't need it now.
                # TODO: Extract Twitter names here
                continue

            if raw_token.lower() == "by":
                # Just survived byline, skip.
                continue

            # Split into finer tokens. Filter out punctuation.
            # Like J.K. Rowling => [J, K, Rowling]
            sub_tokens = nltk.wordpunct_tokenize(raw_token)
            sub_tokens = filter(lambda t: t != ".", sub_tokens)

            # Count some shallow features.
            sb_total = len(sub_tokens)
            sb_caps = 0
            sb_titles = 0
            sb_lowers = 0

            for i, sb in enumerate(sub_tokens):
                if len(sb) == 2 and sb[1] == ".":
                    sub_tokens[i] = sb[0]
                if sb.isupper() and len(sb) > 1:
                    sb_caps += 1
                if sb.islower():
                    sb_lowers += 1
                if sb.istitle():
                    sb_titles += 1

            if len(sub_tokens) == 1:
                # If string contains only one token, it's very unlikely that this is someone's name.

                # However, if original string contained exactly two tokens and they were splitted by comma
                # then probably it was surname and given name in reversed order. Like
                # <a>Zaytsev, <br/>Vladimir</a>
                if len(raw_tokens) == 2 and "," in raw:
                    s_name, f_name = raw_tokens
                    raw_token = "%s %s" % (f_name, s_name)
                    logging.warning("Rare pattern found: %r => %r" % (raw, raw_token))
                    candidates.add(self.canonical(raw_token))
                    continue
                else:
                    if self.RE_TWITTER.match(sub_tokens[0]):
                        logging.warning("Looks like twitter username %r in %r" % (sub_tokens, raw))
                    else:
                        logging.warning("Strange author token %r in %r" % (sub_tokens, raw))
                        continue

            if 0 < sb_caps < sb_total:
                # Count this as organization which is source.
                logging.warning("This is probably organization name %r in %r" % (sub_tokens, raw))
                entity = Entity(name=self.canonical(raw_token, title=False),
                                ent_type=Entity.TYPE.ORG,
                                ent_rel=Entity.REL.SOURCE,
                                is_classified=True)
                entities.append(entity)
                continue

            if sb_caps == 0 and 0 < sb_titles <= sb_lowers:
                logging.warning("Probably just a regular string %r in %r." % (sub_tokens, raw))
                continue

            if len(raw_token) == 0:
                # Wat?
                continue

            if sb_total >= 4:
                # Try to use classifier, looks like a too long sequence.
                if sb_titles >= 5 or sb_caps >= 5:
                    # Ok, this is definitely too long to be someone's name! Skip.
                    continue

            # If candidate survived, add it.
            candidates.add(self.canonical(raw_token))

        # Convert string into entity objects.
        for candidate in candidates:
            author_entity = Entity(name=candidate,
                                   ent_rel=Entity.REL.AUTHOR,
                                   ent_type=Entity.TYPE.PER,
                                   is_classified=True)
            entities.append(author_entity)

        print raw_entity.raw, entities

        return entities


class DateNormalizer(INormalizer):
    """
    TODO(zaytsev@usc.edu):
    """

    MAX_REASONABLE_YEAR = datetime.datetime.now().year + 10
    MIN_REASONABLE_YEAR = 1800

    DIGITS = "0123456789"

    RE_DATE_1 = re.compile("^\d{8}$")
    RE_DATE_2 = re.compile("^\d{14}$")
    RE_DATE_3 = re.compile("^(.*\D)?(\d{4})\-(\d{2})\-(\d{2})(\D.*)?")
    RE_DATE_4 = re.compile("^(.*\D)?(\d{4})/(\d{2})/(\d{2})(\D.*)?")

    def __init__(self):

        self.date_constants = parsedatetime.Constants()
        self.date_calendar = parsedatetime.Calendar(self.date_constants)

    def is_valid_date(self, year, month, day):
        if year > self.MAX_REASONABLE_YEAR or year < self.MIN_REASONABLE_YEAR:
            return False
        try:
            date = datetime.datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize(self, raw_date_str):
        """
        Tries to map input string into normalized date representation "YYYY.MM.DD".
        Assumes that input has exactly one date.
        """

        # Check if input has at least one digit.
        has_digits = False
        for char in raw_date_str:
            if char in self.DIGITS:
                has_digits = True
                break
        if not has_digits:
            return self.EMPTY_RETURN

        norm_raw_date_str = raw_date_str.lstrip().rstrip()

        # Recognize dates like exact "YYYYMMDD"
        if self.RE_DATE_1.match(norm_raw_date_str):
            year = int(norm_raw_date_str[:4])
            month = int(norm_raw_date_str[4:6])
            day = int(norm_raw_date_str[6:])
            if self.is_valid_date(year, month, day):
                return "%04d.%02d.%02d" % (year, month, day)

        # Recognize dates like exact "YYYYMMDD\d{4}"
        if self.RE_DATE_2.match(norm_raw_date_str):
            year = int(norm_raw_date_str[:4])
            month = int(norm_raw_date_str[4:6])
            day = int(norm_raw_date_str[6:8])
            if self.is_valid_date(year, month, day):
                return "%04d.%02d.%02d" % (year, month, day)

        # Recognize dates like "*YY-DD-MM*"
        if self.RE_DATE_3.match(norm_raw_date_str):
            [(_, year, month, day, _)] = self.RE_DATE_3.findall(norm_raw_date_str)
            year, month, day = int(year), int(month), int(day)
            if self.is_valid_date(year, month, day):
                return "%04d.%02d.%02d" % (year, month, day)

        # Recognize dates like "*YY/DD/MM*"
        if self.RE_DATE_4.match(norm_raw_date_str):
            [(_, year, month, day, _)] = self.RE_DATE_4.findall(norm_raw_date_str)
            year, month, day = int(year), int(month), int(day)
            if self.is_valid_date(year, month, day):
                return "%04d.%02d.%02d" % (year, month, day)

        (year, month, day, _, _, _, _, _, _), parsed = self.date_calendar.parse(raw_date_str)
        if parsed > 0 and year <= self.MAX_REASONABLE_YEAR:
            return "%04d.%02d.%02d" % (year, month, day)

        return self.EMPTY_RETURN


class ArticleNormalizer(INormalizer):
    """
    TODO(zaytsev@usc.edu):
    """

    def __init__(self):
        self.date_normalizer = DateNormalizer()
        self.author_normalizer = AuthorNormalizer()

    def normalize_dates(self, raw_date_strs):
        norm_dates = (self.normalize_date(date) for date in raw_date_strs)
        norm_dates = (norm_date for norm_date in norm_dates if len(norm_date) > 0)
        return list(set(norm_dates))

    def normalize_date(self, raw_date_str):
        return self.date_normalizer.normalize(raw_date_str)

    def normalize_authors(self, candidates, article=None):
        entities = []
        for candidate in candidates:
            if candidate.is_classified:
                entities.append(candidate)
            else:
                for found_entity in self.normalize_author(candidate, article):
                    entities.append(found_entity)
        return entities

    def normalize_author(self, candidate, article=None):
        return self.author_normalizer.classify_author_string(candidate, article)


class AuthorExtractor(object):
    """
    TODO(zaytsev@usc.edu):
    """

    ATTRS = ("name", "rel", "itemprop", "class", "id")
    VALS =  ("author", "byline")

    SOCIAL_EXTRACTORS = [
        (re.compile(r"^https?://www\.youtube\.com.*$"), "//*[@id=\"watch7-user-header\"]/div[1]/a[1]", "youtube"),
    ]

    def __init__(self, parser):
        self.parser = parser

    def extract(self, article):
        """
        Ported from: https://github.com/codelucas/newspaper/blob/master/newspaper/extractors.py
        Fetch the authors of the article, return as a list
        Only works for english articles and known social websites.
        """

        doc = article.clean_doc
        matches = []
        authors = []
        names = []

        # Check if it is known social site.
        for url_pattern, xpath, domain in self.SOCIAL_EXTRACTORS:
            if url_pattern.match(article.url):
                found = doc.xpath(xpath)
                if len(found) == 0:
                    logging.warning("Found 0 elements in '%s'" % article.url)
                else:
                    names = map(self.parser.get_content, found)
                    names = (name.rstrip("\r\n\t ").lstrip("\r\n\t ") for name in names)
                    names = (name for name in names if len(name) > 0)
                    for w_name in names:
                        web_names = [(domain, w_name)]
                        author = Entity(name=w_name,
                                        web_names=web_names,
                                        ent_rel=Entity.REL.AUTHOR,
                                        ent_type=Entity.TYPE.UNK,
                                        is_classified=True)
                        authors.append(author)
                    return authors

        # Try popular attributes.
        for attr in self.ATTRS:
            for val in self.VALS:
                found = self.parser.get_by_attr(doc, attr=attr, value=val)
                matches.extend(found)

        # Extract text content from found elements.
        for match in matches:
            content = self.parser.get_content(match).rstrip("\r\n\t ").lstrip("\r\n\t ")

            if len(content) > 0:
                names.append(content)

        # Filter out duplicated.
        unique_names_set = set()
        unique_names = []
        for w_name in names:
            if w_name.lower() in unique_names_set:
                continue
            unique_names.append(w_name)
            unique_names_set.add(w_name.lower())

        # Create entries
        for w_name in unique_names:
            author = Entity(raw=w_name, is_classified=False)
            authors.append(author)

        return authors


class ArticleAttrExtractor(object):
    """
    Class for extracting article attributes from HTML markup.
    """

    DIGITS = re.compile(u"\d", re.UNICODE)
    ATTRS = ["name", "rel", "itemprop", "class", "id"]
    VALS = ["author", "byline"]
    NS = "http://exslt.org/regular-expressions"
    SELECTOR = "descendant-or-self::*"

    def __init__(self, config=None):
        self.parser = ArticleParser()
        self.authors_extractor = AuthorExtractor(self.parser)

        if config is None:
            config = newspaper.configuration.Configuration()
            config.fetch_images = False
        self.config = config

    def parse(self, url, html):
        rdoc = readability.Document(html)
        summary = rdoc.summary()
        lang_id, _ = langid.classify(summary)
        article = newspaper.Article(url, config=self.config, language=lang_id)
        article.set_html(html)
        article.parse()
        return article

    def download_parse(self, url):
        article = newspaper.Article(url, config=self.config)
        article.download()
        article.parse()
        return article

    def extract_images(self, document):
        return [document.top_image]

    def extract_sources(self, document):
        return []

    def extract_title(self, document):
        return []

    def extract_authors(self, article):
        return self.authors_extractor.extract(article)

    def extract_dates(self, document):
        return []