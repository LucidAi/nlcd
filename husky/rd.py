# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

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
                 authors=None):

        self.ref_id = ref_id
        self.url = url
        self.html = html
        self.text = text
        self.title = title
        self.sources = sources
        self.pub_date = pub_date
        self.authors = authors


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
            sentences = sanitize_sentence(sentences)

            for sent in sentences:
                if sent in self.text_index:
                    self.text_index[sent].add(entry.ref_id)
                else:
                    self.text_index[sent] = {entry.ref_id}

    def find_text_references(self, entry):

        sentences = self.text_util.sent_tokenize(entry.text) + [entry.title]
        quotes = self.text_util.extract_quoted(entry.text)
        sentences = self.text_util.select_segments(sentences, quotes, min_size=5)
        sentences = sanitize_sentence(sentences)

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


    def find_cross_references(self, sent_window_size=3):


        found_links = set()

        for entry in self.iterentries():

            entry_refs = self.find_text_references(entry)

            found_links.update(entry_refs)

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


    def print_titles(self):
        for entry in self.id2entry.itervalues():
            print "\t * %s" % entry.title

    def __repr__(self):

        return "<RefIndex(entries=%d)>" % len(self.id2entry)


def sanitize_sentence(sentences):
    sanitized = []
    for s in sentences:
        s = s.lower()
        sanitized.append(s)
    return sanitized
