# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import logging

from husky.textutil import TextUtil


class ReferenceEntry(object):

    def __init__(self,
                 ref_id=None,
                 url=None,
                 html=None,
                 text=None,
                 title=None,
                 sources=None,
                 pub_date=None,
                 authors=None,
                 body=None):

        self.ref_id = ref_id
        self.url = url
        self.html = html
        self.text = text
        self.title = title
        self.sources = sources
        self.pub_date = pub_date
        self.authors = authors
        self.body = body


class ReferenceIndex(object):

    """
    Index
    """

    def __init__(self, entries):

        self.id2entry = {}
        self.text_index = {}

        self.text_util = TextUtil()

        for entry in entries:
            self.id2entry[entry.ref_id] = entry

    def iterentries(self):
        return self.id2entry.itervalues()

    def index(self):

        for entry in self.id2entry.itervalues():

            sentences = self.text_util.sent_tokenize(entry.text) + [entry.title]
            quotes = self.text_util.extract_quoted(entry.text)
            sentences = self.text_util.select_segments(sentences, quotes, min_size=5)
            sentences = sanitize_sentences(sentences)

            for sent in sentences:
                if sent in self.text_index:
                    self.text_index[sent].add(entry.ref_id)
                else:
                    self.text_index[sent] = {entry.ref_id}

    def find_text_references(self, entry):

        sentences = self.text_util.sent_tokenize(entry.text) + [entry.title]
        quotes = self.text_util.extract_quoted(entry.text)
        sentences = self.text_util.select_segments(sentences, quotes, min_size=5)
        sentences = sanitize_sentences(sentences)

        sent_refs = {}

        for sent in sentences:

            found = self.text_index.get(sent)

            for ref_id in found:
                if ref_id == entry.ref_id:
                    continue
                if sent in sent_refs:
                    sent_refs[sent].add(ref_id)
                else:
                    sent_refs[sent] = {ref_id}

        if len(sent_refs) == 0:
            return []

        uniq_refs = set()
        for ref_id_set in sent_refs.itervalues():
            uniq_refs.update(ref_id_set)

        ref_pairs = [(ref_id, entry.ref_id) for ref_id in uniq_refs]

        return ref_pairs


    def extract_query_sentence(self, entry, trim=32):
        sentences = self.text_util.sent_tokenize(entry.text) + [entry.title]
        quotes = self.text_util.extract_quoted(entry.text)
        sentences = self.text_util.select_segments(sentences, quotes, min_size=5)
        sentences = [self.text_util.simplified_text(s) for s in sentences]
        if trim is not None and trim > 0:
            for i in xrange(len(sentences)):
                sentences[i] = " ".join(sentences[i].split()[:trim])
        return sentences

    def extract_references(self, entries):
        found_links = set()
        for entry in entries:
            entry_refs = self.find_text_references(entry)
            found_links.update(entry_refs)
        return found_links

    def fuzzy_extract_references(self, entries):

        entries = list(entries)
        sentence2entry = {}

        # Extract sentences
        logging.info("Extracting sentences.")
        for entry in entries:

            q_sentences = self.extract_query_sentence(entry, trim=32)

            for sent in q_sentences:

                if sent not in sentence2entry:
                    sentence2entry[sent] = {entry.ref_id}
                else:
                    sentence2entry[sent].add(entry.ref_id)

        # Compile regexes
        logging.info("Compiling regexes.")
        sentence2regex = {}
        for sent in sentence2entry.iterkeys():

            if sent not in sentence2regex:
                regex = self.text_util.compile_fuzzy_pattern(sent)
                sentence2regex[sent] = regex
        logging.info("Compiled %d." % len(sentence2regex))

        # Find text matches
        logging.info("Fuzzy matching.")

        entry2matches = {}

        for i, entry in enumerate(entries):

            entry2matches[entry.ref_id] = set()

            for sent, regex in sentence2regex.iteritems():

                if self.text_util.ffs(entry.body, sent, regex):

                    sentence_entries = sentence2entry[sent]

                    for ref_id in sentence_entries:

                        if ref_id == entry.ref_id:
                            continue

                        entry2matches[entry.ref_id].add(ref_id)

            logging.info("Done %d/%d." % (len(entries), i + 1))

        found_pairs = []
        for entry, matches in entry2matches.iteritems():
            for m in matches:
                found_pairs.append((entry, m))

        return found_pairs

    def find_cross_references(self, sent_window_size=3):

        # sentence2id = {}
        #
        # for entry in self.
        #
        #
        # fuzzy_patterns = {}
        #

        found_links = self.fuzzy_extract_references(self.iterentries())
        all_ids = [entry.ref_id for entry in self.iterentries()]

        import networkx as nx
        import matplotlib.pyplot as plt

        dg = nx.DiGraph()
        # dg.add_nodes_from(found_links)
        dg.add_edges_from(found_links)


        nodes = set(dg.nodes_iter())
        pos = nx.spring_layout(dg, iterations=20)

        labels = {entry.ref_id: entry.title for entry in self.iterentries() if entry.ref_id in nodes}

        nx.draw(dg, pos=pos)
        nx.draw_networkx_labels(dg, pos, labels)
        plt.show()

        print "Total", len(all_ids)
        print "Found", len(found_links)

        return found_links

    def print_titles(self):
        for entry in self.id2entry.itervalues():
            print entry.ref_id, "\t * %s" % entry.title

    def __repr__(self):

        return "<RefIndex(entries=%d)>" % len(self.id2entry)


def sanitize_sentences(sentences):
    sanitized = []
    for s in sentences:
        s = s.lower()
        sanitized.append(s)
    return sanitized
