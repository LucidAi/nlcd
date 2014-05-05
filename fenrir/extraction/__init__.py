# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>


NLCD_TO_NLTK_LANG = {
    "en": "english",
    "ru": "russian",
    "de": "german",
    "it": "italian",
}

NLTK_TO_NLCD_LANG = {nltk:nlcd for nlcd,nltk in NLCD_TO_NLTK_LANG.iteritems()}