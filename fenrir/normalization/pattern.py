# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import datetime
import parsedatetime

MAX_REASONABLE_YEAR = datetime.datetime.now().year + 10


class PatterMatchNormalizer(object):

    RE_DATE_1 = re.compile("^\d{8}$")
    RE_DATE_2 = re.compile("^\d{14}$")
    RE_DATE_3 = re.compile("^\d{4}\-\d{2}\-\d{2}$")
    RE_DATE_4 = re.compile("\d{4}\-\d{2}\-\d{2}T.*")

    RE_PERSONS_1 = re.compile(".* and .*")

    def __init__(self):
        self.date_constants = parsedatetime.Constants()
        self.date_calendar = parsedatetime.Calendar(self.date_constants)

    def normalize_date(self, raw_date_str):

        norm_raw_date_str = raw_date_str.lstrip().rstrip()

        if self.RE_DATE_1.match(norm_raw_date_str):
            year = int(norm_raw_date_str[:4])
            month = int(norm_raw_date_str[4:6])
            day = int(norm_raw_date_str[6:])
            if year <= MAX_REASONABLE_YEAR:
                return "%04d.%02d.%02d" % (year, month, day)

        if self.RE_DATE_2.match(norm_raw_date_str):
            year = int(norm_raw_date_str[:4])
            month = int(norm_raw_date_str[4:6])
            day = int(norm_raw_date_str[6:8])
            if year <= MAX_REASONABLE_YEAR:
                return "%04d.%02d.%02d" % (year, month, day)

        if self.RE_DATE_3.match(norm_raw_date_str):
            year = int(norm_raw_date_str[:4])
            month = int(norm_raw_date_str[5:7])
            day = int(norm_raw_date_str[8:10])
            if year <= MAX_REASONABLE_YEAR:
                return "%04d.%02d.%02d" % (year, month, day)

        if self.RE_DATE_4.match(norm_raw_date_str):
            year = int(norm_raw_date_str[:4])
            month = int(norm_raw_date_str[5:7])
            day = int(norm_raw_date_str[8:10])
            if year <= MAX_REASONABLE_YEAR:
                return "%04d.%02d.%02d" % (year, month, day)

        (year, month, day, _, _, _, _, _, _), parsed = self.date_calendar.parse(raw_date_str)
        if parsed > 0 and year <= MAX_REASONABLE_YEAR:
            return "%04d.%02d.%02d" % (year, month, day)

        return ""

    def normalize_persons(self, raw_persons_str):
        names = []


        norm_raw_persons_str = raw_persons_str.lstrip().rstrip()

        if self.RE_PERSONS_1.match(raw_persons_str):
            names.extend(norm_raw_persons_str.split(" and "))


        names = [name for name in names if len(name) < 30]

        return names