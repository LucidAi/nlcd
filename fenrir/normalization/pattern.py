# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import abc
import string
import logging
import datetime
import parsedatetime

MAX_REASONABLE_YEAR = datetime.datetime.now().year + 10
MIN_REASONABLE_YEAR = 1800


class INormalizer(object):
    __metaclass__ = abc.ABCMeta
    EMPTY_RETURN = "<NONE>"


class PatterMatchNormalizer(INormalizer):

    DIGITS = "0123456789"

    RE_DATE_1 = re.compile("^\d{8}$")
    RE_DATE_2 = re.compile("^\d{14}$")
    RE_DATE_3 = re.compile("^(.*\D)?(\d{4})\-(\d{2})\-(\d{2})(\D.*)?")
    RE_DATE_4 = re.compile("^(.*\D)?(\d{4})/(\d{2})/(\d{2})(\D.*)?")

    RE_PERSONS_1 = re.compile(".* and .*")

    def __init__(self):
        self.date_constants = parsedatetime.Constants()
        self.date_calendar = parsedatetime.Calendar(self.date_constants)

    def normalize_dates(self, raw_date_strs):
        norm_dates = (self.normalize_date(date) for date in raw_date_strs)
        norm_dates = (norm_date for norm_date in norm_dates if len(norm_date) > 0)
        return list(set(norm_dates))

    def is_valid_date(self, year, month, day):
        if year > MAX_REASONABLE_YEAR or year < MIN_REASONABLE_YEAR:
            return False
        try:
            date = datetime.datetime(year, month, day)
            return True
        except ValueError:
            return False

    def normalize_date(self, raw_date_str):
        """Tries to map input string into normalized date representation "YYYY.MM.DD".
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
        if parsed > 0 and year <= MAX_REASONABLE_YEAR:
            return "%04d.%02d.%02d" % (year, month, day)

        return self.EMPTY_RETURN

    def normalize_authors(self, raw_author_strs):
        norm_authors = (self.normalize_author(author) for author in raw_author_strs)
        norm_authors = (norm_author for norm_author in norm_authors if len(norm_author) > 0)
        return list(set(norm_authors))

    def normalize_author(self, raw_persons_str):
        names = []
        norm_raw_persons_str = raw_persons_str.lstrip().rstrip()

        if self.RE_PERSONS_1.match(raw_persons_str):
            names.extend(norm_raw_persons_str.split(" and "))

        return ""
