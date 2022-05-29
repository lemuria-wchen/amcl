from sklearn.metrics import cohen_kappa_score
from itertools import combinations


ARGUMENT_TYPE = [0, 1, 2, 3, 4]


def cohen_kappa_score_arg_relation(y1, y2, zero_val=0.01):
    y1_set, y2_set = set(), set()
    for item in y1:
        y1_set.add(tuple(item))
    for item in y2:
        y2_set.add(tuple(item))

    if len(y1_set) == 0 and len(y2_set) == 0:
        return zero_val
    else:
        return (len(y1_set.intersection(y2_set)) + 0.01) / (len(y1_set.union(y2_set)) + 0.01)


def agreement_arg_type(annotated_label):
    score = []
    for y1, y2 in combinations(annotated_label, 2):
        score.append(cohen_kappa_score(y1, y2, labels=ARGUMENT_TYPE))
    return sum(score) / len(score)


def agreement_arg_relation(annotated_label, zero_val=0.01):
    score = []
    for y1, y2 in combinations(annotated_label, 2):
        score.append(cohen_kappa_score_arg_relation(y1, y2, zero_val))
    return sum(score) / len(score)


def agreement_arg_type_double(y1, y2):
    return cohen_kappa_score(y1, y2, labels=ARGUMENT_TYPE)


def agreement_arg_relation_double(y1, y2, zero_val=0.01):
    return cohen_kappa_score_arg_relation(y1, y2, zero_val)
