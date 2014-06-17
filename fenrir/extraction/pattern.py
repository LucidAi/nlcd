# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import jsonpath_rw


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
