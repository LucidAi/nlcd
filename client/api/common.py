# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import datetime


class NlcdApiError(Exception): pass
class NlcdApi400Error(NlcdApiError): pass
class NlcdApi500Error(NlcdApiError): pass
class NlcdApi501Error(NlcdApiError): pass
class NlcdApi503Error(NlcdApiError): pass


def format_iso_date(datetime):
    """Formats `datetime` in following format '%Y-%m-%d'"""
    return datetime.strftime("%Y-%m-%d")


def format_iso_time(datetime):
    """Formats `datetime` in following format '%H:%M:%S'"""
    return datetime.strftime("%H:%M:%S")


def format_iso_datetine(datetime):
    """Formats `datetime` in following format '%Y-%m-%dT%H:%M:%S'"""
    return datetime.strftime("%Y-%m-%dT%H:%M:%S")


def parse_iso_date(string):
    """Parses the following date format '%Y-%m-%d'"""
    pass


def parse_iso_time(string):
    """Parses the following time format '%H:%M:%S'"""
    pass


def parse_iso_datetime(string):
    """Parses the following time-stamp format '%Y-%m-%dT%H:%M:%S'"""
    pass
