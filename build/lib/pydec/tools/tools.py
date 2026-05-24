# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Program operational functions for single segments or functions.

"""
import numpy as np


def element_counter(segment):
    """
    Count the considered segment length.

    """
    return np.sum(segment[1:][::2] - segment[:-1][::2] - 1)


def local_mean(segments, function):
    """
    Compute the local mean in the gien ranged of the sequences
    of the function values.

    """
    sum_values = 0
    for segment in segments:
        sum_values += np.sum(function[np.arange(segment[0], segment[1])])

    elements_segment = element_counter(segments)
    return sum_values / elements_segment


def check_segment_consistency(segments):
    """
    Make sure that the segments are correctly loaded.

    """
    return np.all(segments.flatten()[:-1] <= segments.flatten()[1:])
