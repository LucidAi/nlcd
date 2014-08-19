# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

class Entity(object):
    """
    Definition of entity concept.
    """

    class TYPE(object):
        UNK = "u"     #
        PER = "p"     #
        ORG = "o"     #

    class REL(object):
        UNK = "u"     #
        AUTHOR = "a"  #
        SOURCE = "s"  #

    def __init__(self,
                 raw=None,
                 name=None,
                 web_names=None,
                 synonyms=None,
                 ent_type=TYPE.UNK,
                 ent_rel=REL.UNK,
                 is_classified=False):
        """
        :param raw: str()
        :param name: str()
        :param web_names: sequence((str(), str())
        :param synonyms: sequence(str())
        :param ent_type: int()
        :param ent_rel: int()
        :param is_classified: bool()
        """

        if name is None and raw is None and web_names is not None and synonyms is not None:
            raise ValueError("At least one entity name should be known.")

        # Raw string representing this entity in text.
        self.raw = raw

        # Is classifier was applied. If True, then class and ent_rel are not `UNK`.
        if is_classified and (ent_type == self.TYPE.UNK and ent_rel == self.REL.UNK):
            raise ValueError("Entity cannot have UNK type or rel if it's classified.")
        if not is_classified and (ent_type != self.TYPE.UNK or ent_rel != self.REL.UNK):
            raise ValueError("Entity cannot have not UNK type or rel and be not classified.")
        self.__is_classified = is_classified

        # Just name of entity.
        if name is not None:
            self.name = name.encode("utf-8")
        else:
            self.name = None

        # Dictionary of known Web names.
        self.web_names = {}
        if web_names is not None:
            for domain, w_name in web_names:
                self.web_names[domain.encode("utf-8")] = w_name.encode("utf-8")

        # Other known names of entity
        if synonyms is not None:
            self.synonyms = set((s.encode("utf-8") for s in synonyms))
        else:
            self.synonyms = set()

        # Relation to articles (author or source)
        self.ent_rel = ent_rel

        # Type of entity: person, organization, place, etc.
        self.ent_type = ent_type

        # Some additional features of raw representation
        self.raw_source_line = -1
        self.raw_total_lines = -1

    @property
    def is_classified(self):
        return self.__is_classified

    def set_classified_data(self, ent_rel, ent_type):
        if ent_type == self.TYPE.UNK or ent_rel == self.REL.UNK:
            raise ValueError("Entity cannot have UNK type or rel if it's classified.")
        self.ent_rel = ent_rel
        self.ent_type = ent_type
        self.__is_classified = True

    def set_name(self, name):
        self.name = name.encode("utf-8")

    def add_synonym(self, synonym):
        self.synonyms.add(synonym.encode("utf-8"))

    def add_web_name(self, domain, w_name):
        domain = domain.encode("utf-8")
        w_name = w_name.encode("utf-8")
        if domain in self.web_names:
            prev_w_name = self.web_names[domain]
            if w_name != self.web_names[domain]:
                raise ValueError("Unable to add new Web name."
                                 "This entity is already known as %s at %s." % (prev_w_name, domain))
        self.web_names[domain] = w_name

    def __repr__(self):
        if self.name is None and len(self.web_names) == 0 and len(self.synonyms) == 0:
            entity = ["raw=%r" % self.raw.encode("utf-8")]
        else:
            entity = []
            if self.name is not None:
                entity.append(self.name)
            if len(self.web_names) > 0:
                web_names = self.web_names.itervalues()
                entity.append("w_names=[%s]" % ",".join((str(w_name) for w_name in web_names)))
            if len(self.synonyms) > 0:
                entity.append("synonyms=[%s]" % ",".join(self.synonyms))
        entity.append(self.ent_type + self.ent_rel)
        repr_str = "<Entity(%s)>" % ";".join(entity)
        return repr_str