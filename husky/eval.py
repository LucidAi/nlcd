# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re

from husky.textutil import TextUtil


def compare_titles(p_title, g_title, k=3, from_beginning=True):

    if p_title == g_title:
        return True

    if p_title is None or g_title is None:
        return False

    p_words = p_title.split()
    g_words = g_title.split()

    if len(g_words) < k:
        k = len(g_words)

    for i in xrange(k):

        if from_beginning:
            j = i
        else:
            j = -(i + 1)

        if p_words[j] != g_words[j]:
            return False

    return True


def compute_title_prf(eval_data):

    text_util = TextUtil()

    gold_data = [entry[0] for entry in eval_data]

    gold_eval_out = [None] * len(eval_data)
    eval_out = []

    for method_id in xrange(1, len(eval_data[0])):

        method_data = [entry[method_id] for entry in eval_data]
        method_eval_out = []

        found_n = 0
        correct_n = 0
        data_size = 0

        for i in xrange(len(eval_data)):

            gold = gold_data[i]
            pred = method_data[i]

            gold = text_util.simplified_text(gold) if gold != "<NONE>" and gold != "" else None
            pred = text_util.simplified_text(pred) if pred != "<NONE>" and pred != "" else None

            if gold is not None:
                data_size += 1

            if pred is not None:
                found_n += 1

            correct = compare_titles(pred, gold, 3, True) or compare_titles(pred, gold, 3, False)

            if correct:
                correct_n += 1

            gold_eval_out[i] = gold
            method_eval_out.append((pred, str(int(not correct))))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r) * 2

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
            method_eval_out.append((" , ".join(sorted(pred)), str(int(error_n))))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r) * 2

        prf = (p, r, f)

        eval_out.append((prf, method_eval_out))

    return gold_eval_out, eval_out


def compute_sources_prf(eval_data):

    gold_data = [entry[0] for entry in eval_data]

    gold_eval_out = [None] * len(eval_data)
    eval_out = []

    the_pattern = re.compile("^\s*the\s*", re.IGNORECASE | re.UNICODE)

    for method_id in xrange(1, len(eval_data[0])):

        method_data = [entry[method_id] for entry in eval_data]
        method_eval_out = []

        found_n = 0
        correct_n = 0
        data_size = 0

        for i in xrange(len(eval_data)):


            gold = gold_data[i].split(" AND ") if gold_data[i] != "<NONE>" else []
            pred = method_data[i] if method_data[i] is not None else []

            for k in xrange(len(gold)):
                gold[k] = gold[k].lower() if gold[k] != "" else None
                if gold[k] is not None:
                    gold[k] = the_pattern.sub("", gold[k])
                    gold[k] = gold[k].replace(" ", "")
                    gold[k] = gold[k].replace("-", "")

            for k in xrange(len(pred)):
                pred[k] = pred[k].lower() if pred[k] != "" else None
                if pred[k] is not None:
                    pred[k] = the_pattern.sub("", pred[k])
                    pred[k] = pred[k].replace(" ", "")
                    pred[k] = pred[k].replace("-", "")

            gold = frozenset(gold)
            pred = frozenset(pred)

            correct = False

            if len(pred) > 0:
                found_n += 1

            if len(gold) > 0:
                data_size += 1

            for g in gold:
                for p in pred:
                    if g in p:
                        correct = True
                if correct:
                    break

            if correct:
                correct_n += 1

            gold_eval_out[i] = ", ".join(gold)
            method_eval_out.append((", ".join(pred), str(int(not correct))))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r) * 2

        prf = (p, r, f)

        eval_out.append((prf, method_eval_out))

    return gold_eval_out, eval_out


def compute_dates_prf(eval_data):

    gold_data = [entry[0] for entry in eval_data]

    gold_eval_out = [None] * len(eval_data)
    eval_out = []

    s_pattern = re.compile("\s", re.IGNORECASE | re.UNICODE)

    for method_id in xrange(1, len(eval_data[0])):

        method_data = [entry[method_id] for entry in eval_data]
        method_eval_out = []

        found_n = 0
        correct_n = 0
        data_size = 0

        for i in xrange(len(eval_data)):

            gold = gold_data[i] if gold_data[i] != "<NONE>" else None
            pred = min(method_data[i]) if len(method_data[i]) > 0 else None

            if gold is not None:
                gold = s_pattern.sub("", gold)

            if pred is not None:
                found_n += 1

            if gold is not None:
                data_size += 1

            correct = gold == pred

            if gold == pred and gold is not None and pred is not None:
                correct_n += 1

            gold_eval_out[i] = gold
            method_eval_out.append((pred, str(int(not correct))))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r) * 2

        prf = (p, r, f)

        eval_out.append((prf, method_eval_out))

    return gold_eval_out, eval_out
