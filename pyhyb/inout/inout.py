# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Input/output functions for PyHyB.

Handles reading segment files (``.s``), function files
(``.f``), JSON settings files, and saving results to JSON.
"""
from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
import numpy.typing as npt


def save_results(
    filename: str,
    results: dict[str, Any],
) -> None:
    """Serialise *results* to a JSON file.

    Args:
        filename: Destination file path.
        results: A JSON-serialisable dict of results.
    """
    print(f"Results saved in file {filename}")
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(results, fh)


def _read_segment_file(
    filename: str,
) -> npt.NDArray[np.int_]:
    """Read a segment file (``.s``).

    Args:
        filename: Path to the segment file.

    Returns:
        2-D integer array of ``[start, end]`` pairs.
    """
    data = np.loadtxt(filename).astype(int)
    assert len(data.shape) == 2
    return data


def _read_function_file(
    filename: str,
) -> npt.NDArray[np.float64]:
    """Read a function file (``.f``).

    Args:
        filename: Path to the function file.

    Returns:
        1-D float array of values.
    """
    data = np.loadtxt(filename).astype(float)
    assert len(data.shape) == 1
    return data


def read_data_file(
    filename: str,
) -> npt.NDArray[np.int_ | np.float64]:
    """Read an input data file (``.s`` or ``.f``).

    Dispatches to the appropriate reader based on file
    extension.

    Args:
        filename: Path to the input file.

    Returns:
        The loaded data array.

    Raises:
        ValueError: If the file does not exist or has an
            unsupported extension.
    """
    if not os.path.exists(filename):
        raise ValueError(
            f'Input file "{filename}" not existing!'
        )
    if filename.endswith('.s'):
        return _read_segment_file(filename)
    if filename.endswith('.f'):
        return _read_function_file(filename)

    raise ValueError(
        f'Input file "{filename}" NOT supported!'
    )


def parse_settings_file(
    filename: str,
) -> dict[str, Any]:
    """Read a JSON settings file.

    Args:
        filename: Path to the JSON file.

    Returns:
        The parsed settings dictionary.
    """
    with open(
        filename, 'r', encoding='utf-8'
    ) as openfile:
        settings = json.load(openfile)
    return settings
