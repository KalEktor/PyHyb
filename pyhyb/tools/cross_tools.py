# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Cross-comparison functions.

Provides correlation and overlap metrics between paired
segments or function arrays.
"""
from __future__ import annotations

import warnings

import numpy as np
import numpy.typing as npt


def vanilla_pearson(
    function_1: npt.NDArray[np.float64],
    function_2: npt.NDArray[np.float64],
) -> float:
    """Compute the Pearson correlation using pure Python.

    This is a pedagogical implementation that avoids NumPy's
    ``corrcoef``.  Both inputs must be array-like of equal
    length.

    Args:
        function_1: First data array.
        function_2: Second data array.

    Returns:
        The Pearson correlation coefficient.
    """
    xxx = function_1.tolist()
    yyy = function_2.tolist()

    sum_x, sum_y = 0.0, 0.0
    for i_x, i_y in zip(xxx, yyy):
        sum_x += i_x
        sum_y += i_y

    mean_x = sum_x / len(xxx)
    mean_y = sum_y / len(yyy)

    num, den1, den2 = 0.0, 0.0, 0.0
    for i_x, i_y in zip(xxx, yyy):
        num += (i_x - mean_x) * (i_y - mean_y)
        den1 += (i_x - mean_x) ** 2
        den2 += (i_y - mean_y) ** 2

    return num / (den1 ** 0.5) / (den2 ** 0.5)


def pearson(
    function_1: npt.NDArray[np.float64],
    function_2: npt.NDArray[np.float64],
) -> float:
    """Compute the Pearson correlation coefficient.

    Uses :func:`numpy.corrcoef` for numerical stability.

    Args:
        function_1: First data array.
        function_2: Second data array.

    Returns:
        The Pearson correlation coefficient.
    """
    return float(
        np.corrcoef(function_1, function_2)[1][0]
    )


# ----------------------------------------------------------
# Deprecated aliases (kept for backwards compatibility)
# ----------------------------------------------------------
def vanilla_person(
    function_1: npt.NDArray[np.float64],
    function_2: npt.NDArray[np.float64],
) -> float:
    """Compute Pearson correlation (vanilla).

    .. deprecated::
        Use :func:`vanilla_pearson` instead.
    """
    warnings.warn(
        "vanilla_person() is deprecated, "
        "use vanilla_pearson() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return vanilla_pearson(function_1, function_2)


def person(
    function_1: npt.NDArray[np.float64],
    function_2: npt.NDArray[np.float64],
) -> float:
    """Compute Pearson correlation.

    .. deprecated::
        Use :func:`pearson` instead.
    """
    warnings.warn(
        "person() is deprecated, "
        "use pearson() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return pearson(function_1, function_2)


def segment_overlap(
    segments_1: npt.NDArray[np.int_],
    segments_2: npt.NDArray[np.int_],
) -> int:
    """Count overlapping elements between segment lists.

    Each segment is a ``[start, end)`` pair.  The function
    iterates over all segment pairs and sums the length of
    their intersection.

    Args:
        segments_1: First list of ``[start, end)`` pairs.
        segments_2: Second list of ``[start, end)`` pairs.

    Returns:
        Total number of overlapping indices.
    """
    cnt = 0
    for seg_1 in segments_1:
        for seg_2 in segments_2:
            if seg_1[1] < seg_2[0]:
                break
            if seg_2[1] < seg_1[0]:
                continue

            cnt += np.intersect1d(
                np.arange(seg_1[0], seg_1[1]),
                np.arange(seg_2[0], seg_2[1]),
            ).shape[0]
    return cnt
