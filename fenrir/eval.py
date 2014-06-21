# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

import re
import datetime
import dateutil.relativedelta

from fenrir.normalization.pattern import INormalizer

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


def evaluate_extraction(output_rows):
    # output_rows = [(input_str, true_value, pred_value, is_correct)]
    total_values = len(output_rows)
    correct = sum((row[-1] for row in output_rows))
    total_found = 0
    correct_found = 0
    total_non_empty = 0
    for input_str, true_value, pred_value, is_correct in output_rows:
        if pred_value != INormalizer.EMPTY_RETURN:
            total_found += 1
            if pred_value == true_value:
                correct_found += 1
        if true_value != INormalizer.EMPTY_RETURN:
            total_non_empty += 1
    precision = float(correct_found) / total_found
    recall =  float(correct_found) / total_non_empty
    accuracy = correct / float(total_values)
    return accuracy, precision, recall



