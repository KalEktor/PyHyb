# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Program operational functions for cross checks between
different segments or functions.

"""
import numpy as np


def vanilla_person(function_1, function_2):
    """
    Compute Person cross correlation function between different functions
    with Vanilla Python.

    """
    xxx = function_1.tolist()
    yyy = function_2.tolist()

    sum_x, sum_y = 0, 0
    for i_x, i_y in zip(xxx, yyy):
        sum_x += i_x
        sum_y += i_y

    mean_x = sum_x/len(xxx)
    mean_y = sum_y/len(yyy)

    num, den1, den2 = 0, 0, 0
    for i_x, i_y in zip(xxx, yyy):
        num += (i_x-mean_x)*(i_y-mean_y)
        den1 += ((i_x-mean_x)**2)
        den2 += ((i_y-mean_y)**2)

    person_coeff = num/(den1**0.5)/(den2**0.5)
    return person_coeff


def person(function_1, function_2):
    """
    Compute Person cross correlation function between different functions.

    """
    return np.corrcoef(function_1, function_2)[1][0]


def segment_overlap(segments_1, segments_2):
    """
    Compute segment overla between different segment files.

    """
    cnt = 0
    for seg_1 in segments_1:
        for seg_2 in segments_2:
            # Taking advantage of segment properties to go faster
            if seg_1[1] < seg_2[0]:
                break
            if seg_2[1] < seg_1[0]:
                continue

            cnt += np.intersect1d(np.arange(seg_1[0], seg_1[1]),
                                  np.arange(seg_2[0], seg_2[1])).shape[0]
    return cnt
