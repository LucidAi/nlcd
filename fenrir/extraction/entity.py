# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import nltk


class NerExtractor(object):

    def apply_truecase(self, tokens):
        tokens = tokens[:]
        for i in xrange(len(tokens)):
            if len(tokens[i]) <= 3 or tokens[i][0] == "@":
                continue
            elif tokens[i].isupper():
                tokens[i] = tokens[i].title()
        return tokens

    def extract_entities(self, texts, truecase=True, set_label=None):
        """Extracts named entites from set of strings.
        
        Args:
            texts (list): Collection of input strings.
        
        Kwargs:
            truecase (bool): If True, method applies heuristic to match true cases of words
                             in texts (improves quality on short strings).
            set_label (str): If not None, then method uses binary classification and label
                             found entities with provided label value. Otherwise uses
                             multiclass classification with default NLTK NE labels.
        
        Returns:
            (set): Set of pairs (entity, label).
        """
        entities = set()
        for text in texts:
            sentences = nltk.sent_tokenize(text)
            sentences = [nltk.word_tokenize(sent) for sent in sentences]
            if truecase:
                for i, sent in enumerate(sentences):
                    sentences[i] = self.apply_truecase(sent)
            sentences = [nltk.pos_tag(sent) for sent in sentences]
            for sent in sentences:
                ner_tree = nltk.ne_chunk(sent, binary=set_label is not None)
                for ne in ner_tree:
                    if hasattr(ne, "node"):
                        entities.add((ne.node, " ".join(l[0] for l in ne.leaves())))
        if set_label is not None:
            entities = [{"label":set_label, "entity": entity} for label,entity in entities]
        else:
            entities = [{"label":label, "entity": entity} for label,entity in entities]

        return entities
