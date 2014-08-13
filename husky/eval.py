#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from husky.textutil import TextUtil


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

            if pred == gold:
                correct_n += 1

            gold_eval_out[i] = gold
            method_eval_out.append((pred, int(pred != gold)))

        p = 0 if found_n == 0 else float(correct_n) / float(found_n)
        r = 0 if data_size == 0 else float(correct_n) / float(data_size)
        f = 0 if p + r == 0 else p * r / (p + r)

        prf = (p, r, f)

        eval_out.append((prf, method_eval_out))

    return gold_eval_out, eval_out