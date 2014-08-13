# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import json
import logging
import datetime

import nltk
import langid
import newspaper
import jsonpath_rw
import readability
import parsedatetime

from husky.entity import Entity
from husky.dicts import Blacklist
from husky.parsers import ArticleParser


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


class DateExtractor(object):

    DEFAULT_CONFIGURATION_PATH = "./distr/patterns/google.cse.json"

    def __init__(self):
        with open(self.DEFAULT_CONFIGURATION_PATH, "rb") as i_fl:
            self.patterns = json.load(i_fl)
        self.util = JsonPatternMatchingUtil()
        self.dates_pattern = self.util.compile(self.patterns, "dates")
        self.snippet_pattern = self.util.compile(self.patterns, "snippet")

    def extract_from_annotation(self, annotation):
        dates = self.util.match(self.dates_pattern, annotation)
        snipped_date = self.util.match_first(self.snippet_pattern, annotation)
        if snipped_date is not None:
            snipped_date = snipped_date[:12].rstrip()
            dates.append(snipped_date)
        return list(set(dates))

    def extract(self, article):
        # logging.warning("Article date extraction is not implemented.")
        return []


class SourcesExtractor(object):

    DEFAULT_CONFIGURATION_PATH = "./distr/patterns/google.cse.json"

    def __init__(self):
        with open(self.DEFAULT_CONFIGURATION_PATH, "rb") as i_fl:
            self.patterns = json.load(i_fl)
        self.blacklist = Blacklist.load(Blacklist.BLACK_SRC)
        self.util = JsonPatternMatchingUtil()
        self.source_pattern = self.util.compile(self.patterns, "sources")

    def extract_from_json(self, annotation):
        sources = self.util.match_unique(self.source_pattern, annotation)
        sources = [s for s in sources if s not in self.blacklist]
        return sources


class AuthorExtractor(object):
    """
    TODO(zaytsev@usc.edu):
    """

    ATTRS = ("name", "rel", "itemprop", "class", "id")
    VALS =  ("author", "byline", "creator")

    SOCIAL_EXTRACTORS = [
        (re.compile(r"^https?://www\.youtube\.com.*$"), "//*[@id=\"watch7-user-header\"]/div[1]/a[1]", "youtube"),
    ]

    MAX_CONTENT_LEN = 120
    MAX_ATTRVAL_ELEMENTS = 10
    MAX_OUTPUT_ENTITIES = 25
    MAX_CONTENT_ELEMENTS = 25

    def __init__(self, parser):
        self.parser = parser
        self.black_attr = Blacklist.load(Blacklist.BLACK_AUTHOR_ATTR)

    def extract(self, article):
        """
        Ported from: https://github.com/codelucas/newspaper/blob/master/newspaper/extractors.py
        Fetch the authors of the article, return as a list
        Only works for english articles and known social websites.
        """

        html, doc = self.parser.get_clean_document(article)
        total_lines = html.count("\n")

        matches = []
        found_entities = []
        names = []

        # Check if it is known social site.
        for url_pattern, xpath, domain in self.SOCIAL_EXTRACTORS:
            if url_pattern.match(article.url):
                found = doc.xpath(xpath)
                if len(found) == 0:
                    logging.warning("Found 0 elements in '%s'" % article.url)
                else:
                    names = map(self.parser.get_content, found)
                    names = (" ".join(name).rstrip("\r\n\t ").lstrip("\r\n\t ") for name in names)
                    names = (name for name in names if len(name) > 0)
                    for w_name in names:
                        web_names = [(domain, w_name)]
                        entity = Entity(name=w_name,
                                        web_names=web_names,
                                        ent_rel=Entity.REL.AUTHOR,
                                        ent_type=Entity.TYPE.UNK,
                                        is_classified=True)
                        found_entities.append(entity)
                    return found_entities

        # Try popular attributes.
        for attr in self.ATTRS:
            for val in self.VALS:
                found = self.parser.get_by_attr(doc, attr=attr, value=val)
                if len(found) <= self.MAX_ATTRVAL_ELEMENTS:
                    found = self.parser.blacklist_elements(found, self.black_attr)
                    matches.extend(found)

        # Extract text content from found elements.
        for mm in matches:
            contents = self.parser.get_content(mm)
            if len(contents) <= self.MAX_CONTENT_ELEMENTS:
                for content in contents:
                    content = content.rstrip("\r\n\t ").lstrip("\r\n\t ")
                    if 0 < len(content) <= self.MAX_CONTENT_LEN:
                        names.append((content, mm.sourceline))

        # Filter out duplicated.
        unique_names_set = set()
        unique_names = []
        for w_name, source_line in names:
            if w_name.lower() in unique_names_set:
                continue
            unique_names.append((w_name, source_line))
            unique_names_set.add(w_name.lower())

        # Create entries
        for w_name, source_line in unique_names:
            entity = Entity(raw=w_name, is_classified=False)
            entity.raw_source_line = source_line
            entity.raw_total_lines = total_lines
            found_entities.append(entity)

        return found_entities


class EntityExtractor(object):
    """
    Class for extracting article attributes from HTML markup.
    """

    def __init__(self, config=None):
        self.sites_blacklist = Blacklist.load(Blacklist.BLACK_DOM)
        self.parser = ArticleParser()

        self.date_extractor = DateExtractor()
        self.source_extractor = SourcesExtractor()
        self.author_extractor = AuthorExtractor(self.parser)

        if config is None:
            config = newspaper.configuration.Configuration()
            config.fetch_images = False
        self.config = config

    def parse_article(self, url, html):
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

    def extract_images(self, article=None, annotation=None):
        return [article.top_image]

    def extract_sources(self, article=None, annotation=None):
        return self.source_extractor.extract_from_json(annotation)

    def extract_titles(self, article=None, annotation=None, select_best=True):
        """
        If select_best is True - returns shortest found title.
        """
        titles = set()
        if len(article.title) > 0:
            titles.add(article.title)
        if select_best:
            if len(titles) == 0:
                return None
            else:
                return min(titles, key=len)
        else:
            return titles

    def extract_authors(self, article=None, annotation=None):
        if article.url in self.sites_blacklist:
            logging.info("Blacklisted %r." % article.url)
            return []
        authors = self.author_extractor.extract(article)
        return authors

    def extract_dates(self, article=None, annotation=None, select_min=True):
        doc_dates = self.date_extractor.extract(article)
        ann_dates = self.date_extractor.extract_from_annotation(annotation)
        dates = set(doc_dates)
        dates.update(ann_dates)
        return list(dates)


class AuthorNormalizer(object):

    RE_NOT_ALLOWED = re.compile("\d|:|\||\+|@|\-|<|>", re.UNICODE)
    RE_BYLINE = re.compile("by[\:\s\|]|from[\:\s]", re.UNICODE | re.IGNORECASE)
    RE_SEP = re.compile(u"[\r\n,;]|\Wand\W", re.UNICODE | re.IGNORECASE)
    RE_SPACE = re.compile(u"\s", re.UNICODE)
    RE_MULTIPLE_SPACES = re.compile(u" +", re.UNICODE)
    RE_BRACKETS = re.compile("\(.*?\)")
    RE_TWITTER = re.compile(u"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9]+)", re.UNICODE)

    MAX_INPUT_LEN = 120
    MIN_NAME_LEN = 5
    MAX_OUTPUT_ENTITIES_COUNT = 10

    def __init__(self):

        # Black and white lists

        self.white_org = Blacklist.load(Blacklist.WHITE_ORG)
        # self.black_org = WordList.load(WordList.BLACK_ORG)

        # self.white_per = WordList.load(WordList.WHITE_PER)
        self.black_per = Blacklist.load(Blacklist.BLACK_PER)

        # self.white_ner = WordList.load(WordList.WHITE_NER)
        self.black_ner = Blacklist.load(Blacklist.BLACK_NER)

    def canonical(self, name_string, title=True):
        name_string = self.RE_MULTIPLE_SPACES.sub(" ", name_string).lstrip().rstrip()
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

        # print "\tRAW:%r" % raw.replace("\n", " ")

        for raw_token in raw_tokens:

            is_ner_blacklisted = False
            is_ner_whitelisted = False
            is_org_blacklisted = False
            is_org_whitelisted = False
            is_per_blacklisted = False
            is_per_whitelisted = False
            ner_type = Entity.TYPE.PER  # Default ner type

            # Clean token. Map multiple spaces into one space character.
            raw_token = self.RE_SPACE.sub(" ", raw_token)
            raw_token = self.RE_MULTIPLE_SPACES.sub(" ", raw_token).lstrip().rstrip()

            # Check if token has not-allowed symbols.
            if bool(self.RE_NOT_ALLOWED.search(raw_token)):
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

            # Apply white and blacklists
            for sb in sub_tokens:

                if sb in self.black_ner:
                    logging.warning("Black-listed NER %r (%r) from %r." % (sb, raw_token, raw_tokens))
                    is_ner_blacklisted = True
                    break

                if sb in self.black_per:
                    logging.warning("Black-listed PER %r (%r) from %r." % (sb, raw_token, raw_tokens))
                    is_per_blacklisted = True
                    break

                if sb in self.white_org:
                    logging.warning("White-listed ORG %r (%r) from %r." % (sb, raw_token, raw_tokens))
                    is_org_whitelisted = True
                    ner_type = Entity.TYPE.ORG
                    break

            # If white/blacklisted then create entity or go to the next raw_token.
            # Else, apply domain specific rules.
            if not(
               is_ner_whitelisted or
               is_ner_blacklisted or
               is_per_whitelisted or
               is_per_blacklisted or
               is_org_whitelisted or
               is_org_blacklisted):

                if len(sub_tokens) == 1:
                    # If string contains only one token, it's very unlikely that this is someone's name.
                    if self.RE_TWITTER.match(sub_tokens[0]):
                        logging.warning("Looks like twitter username %r in %r" % (sub_tokens, raw))
                    else:
                        logging.warning("Strange author token %r in %r" % (sub_tokens, raw))
                        continue

                if 0 < sb_caps < sb_total < 5:
                    # Count this as organization which is source.
                    logging.warning("This is probably organization name %r in %r" % (sub_tokens, raw))
                    ner_type = Entity.TYPE.ORG

                if sb_titles > 0 and sb_lowers > 0:
                    logging.warning("Probably just a regular string %r in %r." % (sub_tokens, raw))
                    is_ner_blacklisted = True

                if len(raw_token) == 0:
                    is_ner_blacklisted = True

                if sb_total >= 4:
                    # Try to use classifier, looks like a too long sequence.
                    if sb_titles >= 5 or sb_caps >= 5:
                        # Ok, this is definitely too long to be someone's name! Skip.
                        is_ner_blacklisted = True

            if is_ner_blacklisted:
                continue
            if is_per_blacklisted and ner_type == Entity.TYPE.PER:
                continue
            if is_org_blacklisted and ner_type == Entity.TYPE.ORG:
                continue

            if len(raw_token) > self.MIN_NAME_LEN:
                name = self.canonical(raw_token, title=ner_type == Entity.TYPE.PER)
                candidates.add((name, ner_type))

        # Convert string into entity objects.
        for name, ner_type in candidates:
            author_entity = Entity(name=name,
                                   ent_rel=Entity.REL.AUTHOR,
                                   ent_type=ner_type,
                                   is_classified=True)
            author_entity.raw_source_line = raw_entity.raw_source_line
            author_entity.raw_total_lines = raw_entity.raw_total_lines
            entities.append(author_entity)

        # print raw_entity.raw, entities
        if len(entities) > self.MAX_OUTPUT_ENTITIES_COUNT:
            return []

        return entities

    def merge_synonyms(self, authors):
        pass


class DateNormalizer(object):
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

    def normalize(self, candidates):
        dates = set()
        for raw_date in candidates:
            norm_date = self.normalize_date(raw_date)
            if norm_date is not None:
                dates.add(norm_date)
        return list(dates)

    def normalize_date(self, candidate):
        """
        Tries to map input string into normalized date representation "YYYY.MM.DD".
        Assumes that input has exactly one date.
        """

        # Check if input has at least one digit.
        has_digits = False
        for char in candidate:
            if char in self.DIGITS:
                has_digits = True
                break
        if not has_digits:
            return None

        norm_raw_date_str = candidate.lstrip().rstrip()

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

        (year, month, day, _, _, _, _, _, _), parsed = self.date_calendar.parse(candidate)
        if parsed > 0 and year <= self.MAX_REASONABLE_YEAR:
            return "%04d.%02d.%02d" % (year, month, day)

        return None


class EntityNormalizer(object):
    """
    TODO(zaytsev@usc.edu):
    """

    def __init__(self):
        self.date_normalizer = DateNormalizer()
        self.author_normalizer = AuthorNormalizer()

    def normalize_dates(self, candidates):
        return self.date_normalizer.normalize(candidates)

    def normalize_authors(self, candidates, article=None):
        entities = {}
        for candidate in candidates:
            if candidate.is_classified:
                if candidate.name not in entities:
                    entities[candidate.name] = candidate
            else:
                for found_entity in self.normalize_author(candidate, article):
                    if found_entity.name not in entities:
                        entities[found_entity.name] = found_entity
        return entities.values()

    def normalize_author(self, candidate, article=None):
        return self.author_normalizer.classify_author_string(candidate, article)