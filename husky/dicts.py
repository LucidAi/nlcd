# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re


class Blacklist(object):
    """
    """
    BLACK_DOM = "./distr/misc/black.dom.txt"

    WHITE_NER = "./distr/misc/white.ner.txt"
    BLACK_NER = "./distr/misc/black.ner.txt"
    WHITE_ORG = "./distr/misc/white.org.txt"
    BLACK_ORG = "./distr/misc/black.org.txt"
    WHITE_PER = "./distr/misc/white.per.txt"
    BLACK_PER = "./distr/misc/black.per.txt"

    BLACK_AUTHOR_ATTR = "./distr/misc/black.author.attr.txt"

    def __init__(self, patterns):
        self.patterns = frozenset(patterns)
        regexes = []
        for regex in self.patterns:
            regexes.append("^%s$" % regex)
        self.entire_re = re.compile("|".join(regexes), re.UNICODE | re.IGNORECASE)

    def __contains__(self, string):
        return bool(self.entire_re.match(string))

    @staticmethod
    def load(file_path):
        with open(file_path, "rb") as i_file:
            patterns = i_file.read().strip().split("\n")
            return Blacklist(patterns)
