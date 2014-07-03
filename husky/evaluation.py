# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import datetime
import dateutil.relativedelta

# y - year
# m - month
# w - week
# d - day
# h - hour
# M - minute
# s - second
RE_DATE_EXPR_1 = re.compile(u"(\d+[ymwdhMs])", re.UNICODE)


def eval_date(expr):
    if expr[1] == "+" or expr[1] == "-":
        computed_date = datetime.datetime.now()
        sign = expr[0]
        shifts = RE_DATE_EXPR_1.findall(expr)
        for shift in shifts:
            unit = shift[-1]
            quantity = int(shift[:-1])
            if unit == "y":
                delta = dateutil.relativedelta.relativedelta(years=quantity)
            if unit == "m":
                delta = dateutil.relativedelta.relativedelta(months=quantity)
            if unit == "w":
                delta = dateutil.relativedelta.relativedelta(weeks=quantity)
            if unit == "d":
                delta = dateutil.relativedelta.relativedelta(days=quantity)
            if unit == "h":
                delta = dateutil.relativedelta.relativedelta(hours=quantity)
            if unit == "M":
                delta = dateutil.relativedelta.relativedelta(minutes=quantity)
            if unit == "s":
                delta = dateutil.relativedelta.relativedelta(seconds=quantity)
            if sign == "+":
                computed_date += delta
            else:
                computed_date -= delta
        computed_date = "%04d.%02d.%02d" % (computed_date.year, computed_date.month, computed_date.day)
        return computed_date
    else:
        today = datetime.datetime.now()
        pattern = expr[1:-1]
        year = "%04d" % today.year
        month = "%02d" % today.month
        day = "%02d" % today.day
        computed_date = pattern.replace("YYYY", year).replace("MM", month).replace("DD", day)
        return computed_date


def compute_arp(eval_entries, eval_dates=False):
    # eval_entries = [(true_values, pred_values)]

    error_rows = []

    total_true_entries = 0
    total_found_entries = 0
    correct_found_entries = 0

    for true_values, pred_values in eval_entries:

        if eval_dates:
            e_pred_values = set()
            for v in pred_values:
                if v.startswith("{"):
                    e_pred_values.add(eval_date(v))
                else:
                    e_pred_values.add(v)

        row_errors = 0
        total_true_entries += len(true_values)
        total_found_entries += len(pred_values)
        for p_val in pred_values:
            if p_val in true_values:
                correct_found_entries += 1
            else:
                row_errors += 1
        for t_val in true_values:
            if t_val not in pred_values:
                row_errors += 1
        error_rows.append(row_errors)

    precision = float(correct_found_entries) / total_found_entries
    recall = float(correct_found_entries) / total_true_entries

    return (precision, recall, 100), error_rows




