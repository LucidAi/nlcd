#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re

from husky.textutil import TextUtil


def compare_titles(title_1, title_2, k=3, from_beginning=True):

    if title_1 == title_2:
        return True

    if title_1 is None or title_2 is None:
        return False

    words_1 = title_1.split()
    words_2 = title_2.split()

    if len(words_1) < k or len(words_2) < k:
        return False

    for i in xrange(k):

        if from_beginning:
            j = i
        else:
            j = -(i + 1)

        if words_1[j] != words_2[j]:
            return False

    return True


def compute_title_prf(eval_data):

    text_util = TextUtil()

    gold_data = [entry[0] for entry in eval_data]
    data_size = len(gold_data)

    gold_eval_out = [None] * data_size
    eval_out = []

    for method_id in xrange(1, len(eval_data[0])):

        method_data = [entry[method_id] for entry in eval_data]
        method_eval_out = []

        found_n = 0
        correct_n = 0

        for i in xrange(data_size):

            gold = gold_data[i]
            pred = method_data[i]

            gold = text_util.simplified_text(gold) if gold != "<NONE>" and gold != "" else None
            pred = text_util.simplified_text(pred) if pred != "<NONE>" and pred != "" else None

            if pred is not None:
                found_n += 1

            correct = compare_titles(pred, gold, 3, True) or compare_titles(pred, gold, 3, False)

            if correct:
                correct_n += 1

            gold_eval_out[i] = gold
            method_eval_out.append((pred, int(not correct)))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r)

        prf = (p, r, f)

        eval_out.append((prf, method_eval_out))

    return gold_eval_out, eval_out


def compute_authors_prf(eval_data):
    gold_data = [entry[0] for entry in eval_data]

    gold_eval_out = [None] * len(gold_data)
    eval_out = []

    for method_id in xrange(1, len(eval_data[0])):

        method_data = [entry[method_id] for entry in eval_data]
        method_eval_out = []

        found_n = 0
        correct_n = 0
        data_size = 0

        for i in xrange(len(eval_data)):

            gold = gold_data[i].split(" AND ") if gold_data[i] != "<NONE>" else []
            pred = method_data[i]

            gold = frozenset([g.lower() for g in gold])
            pred = frozenset([p.lower() for p in pred])

            data_size += len(gold)
            found_n += len(pred)
            error_n = 0

            for p in pred:
                if p in gold:
                    correct_n += 1
                else:
                    error_n += 1

            for g in gold:
                if g not in pred:
                    error_n += 1

            gold_eval_out[i] = " , ".join(sorted(gold))
            method_eval_out.append((" , ".join(sorted(pred)), int(error_n)))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r)

        prf = (p, r, f)

        eval_out.append((prf, method_eval_out))


    return gold_eval_out, eval_out


def compute_sources_prf(eval_data):

    gold_data = [entry[0] for entry in eval_data]
    data_size = len(gold_data)

    gold_eval_out = [None] * data_size
    eval_out = []

    the_pattern = re.compile("^\s*the\s*", re.IGNORECASE | re.UNICODE)

    for method_id in xrange(1, len(eval_data[0])):

        method_data = [entry[method_id] for entry in eval_data]
        method_eval_out = []

        found_n = 0
        correct_n = 0

        for i in xrange(data_size):


            gold = gold_data[i].split(" AND ") if gold_data[i] != "<NONE>" else []
            pred = method_data[i] if method_data[i] is not None else []

            for k in xrange(len(gold)):
                gold[k] = gold[k].lower() if gold[k] != "" else None
                if gold[k] is not None:
                    gold[k] = the_pattern.sub("", gold[k])

            for k in xrange(len(pred)):
                pred[k] = pred[k].lower() if pred[k] != "" else None
                if pred[k] is not None:
                    pred[k] = the_pattern.sub("", pred[k])

            print pred
            print gold
            print

            # if len(pred) > 0
            # found_n += 1
        #
        #     if pred == gold:
        #         correct_n += 1
        #
        #     gold_eval_out[i] = gold
        #     method_eval_out.append((pred, int(pred != gold)))
        #
        # p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        # r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        # f = 0 if p + r == 0 else p * r / (p + r)
        #
        # prf = (p, r, f)
        #
        # eval_out.append((prf, method_eval_out))