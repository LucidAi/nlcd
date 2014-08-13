# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import cgi
import logging


class EntityReference(object):

    def __init__(self, span, match, references, extra_attr=None):
        self.span = span
        self.match = match
        self.references = references
        self.extra_attr = extra_attr


class MarkupChunk(object):

    def __init__(self, text):
        self.c_id = None
        self.text = text
        self.references = []

    def add_ref(self, e_ref):
        self.references.append(e_ref)


class Markup(object):

    def __init__(self, id_str=None, title=None, body_elements=[]):
        self.id_str = id_str
        self.title = title
        self.body_elements = []
        for b_elem in body_elements:
            self.add_body_element(b_elem)

    def add_body_element(self, m_chunk):
        m_chunk.c_id = 1 + len(self.body_elements)
        self.body_elements.append(m_chunk)

    def set_title(self, m_chunk):
        m_chunk.c_id = 0
        self.title = m_chunk

    @staticmethod
    def blank():
        return Markup("husky.markup.Markup", None, [])

    def json(self):
        return {
            "id": self.id_str,
            "title": self.e2json(self.title) if self.title is not None else None,
            "body": [self.e2json(chunk) for chunk in self.body_elements],
        }

    def e2tags(self, element):

        e_id = "%s.%d" % (self.id_str, element.c_id)

        if len(element.references) == 0:
            return [{
                "text": element.text,
                "references": [],
                "tagged": False,
            }]

        tags = []
        prev_end = 0

        element.references.sort(key=lambda r: r.span)

        for i, ref in enumerate(element.references):

            if prev_end > ref.span[0]:

                logging.error("Incorrect reference data found. Text: %s. Chunk: %d. A,B: %d %d." % (
                    ref.match,
                    element.c_id,
                    ref.span[0],
                    ref.span[1],
                ))

            elif prev_end < ref.span[0]:

                tags.append({
                    "text": element.text[prev_end:ref.span[0]],
                    "references": [],
                    "tagged": False,
                })

            tag_id = "%s_%d" % (e_id, i)
            tag_text = element.text[ref.span[0]:ref.span[1]]
            tags.append({
                "tagged": True,
                "text": tag_text,
                "tagId": tag_id,
                "references": ref.references,
            })

            prev_end = ref.span[1]


        if prev_end != len(element.text):

            tags.append({
                "text": element.text[prev_end:len(element.text)],
                "references": [],
                "tagged": False,
            })

        return tags

    def e2json(self, element):
        return {
            "cId": "%s_%d" % (self.id_str, element.c_id),
            "text": element.text,
            "taggedText": self.e2tags(element),
            "references": [{
                "span": list(ref.span),
                "match": ref.match,
                "references": ref.references,
                "extraAttr": ref.extra_attr,
            } for ref in element.references]
        }
