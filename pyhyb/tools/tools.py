# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Single-segment analysis functions.

Provides utilities for counting segment elements, computing
local means over segmented ranges, and validating segment
consistency.
"""
from __future__ import annotations

import numpy as np
import numpy.typing as npt


def element_counter(
    segment: npt.NDArray[np.int_],
) -> np.int_:
    """Count the total number of elements across segments.

    Args:
        segment: A 2-D array of ``[start, end]`` pairs.

    Returns:
        Total element count.
    """
    return np.sum(
        segment[1:][::2] - segment[:-1][::2] - 1
    )


def local_mean(
    segments: npt.NDArray[np.int_],
    function: npt.NDArray[np.float64],
) -> float:
    """Compute the mean of *function* over *segments*.

    Args:
        segments: A list of ``[start, end)`` pairs.
        function: A 1-D array of function values.

    Returns:
        The mean value over all segments.
    """
    sum_values: float = 0
    for segment in segments:
        sum_values += np.sum(
            function[np.arange(segment[0], segment[1])]
        )

    elements_segment = element_counter(segments)
    return sum_values / elements_segment


def check_segment_consistency(
    segments: npt.NDArray[np.int_],
) -> bool:
    """Verify that segments are sorted and non-overlapping.

    Args:
        segments: A 2-D array of ``[start, end]`` pairs.

    Returns:
        ``True`` if segments are consistent.
    """
    return bool(np.all(
        segments.flatten()[:-1] <= segments.flatten()[1:]
    ))
