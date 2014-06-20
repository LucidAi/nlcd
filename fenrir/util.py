# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

from fenrir.normalization.pattern import INormalizer


def evaluate_extraction(output_rows):
    # output_rows = [(input_str, true_value, pred_value, is_correct)]
    total_values=len(output_rows)
    correct = sum((row[-1] for row in  output_rows))
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



