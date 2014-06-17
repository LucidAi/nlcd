# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from abc import ABCMeta
from abc import abstractmethod


class IAnnotator(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def extract_url(self, item):
        raise NotImplemented()

    @abstractmethod
    def extract_title(self, item):
        raise NotImplemented()

    @abstractmethod
    def extract_authors(self, data):
        raise NotImplemented()

    @abstractmethod
    def extract_sources(self, data):
        raise NotImplemented()

    @abstractmethod
    def extract_dates(self, data):
        raise NotImplemented()

    @abstractmethod
    def extract_images(self, data):
        raise NotImplemented()

class Annotation(object):
    """Class for accessing Google CSE annotation data."""

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
