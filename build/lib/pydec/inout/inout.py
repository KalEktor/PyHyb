# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
In and output fucntions of PyDec.

"""
import os
import json
import numpy as np


def save_results(filename, results):
    """
    Save results in a json format.

    """
    print(f"Results saved in file {filename}")
    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile)


def _read_segment_file(filename):
    """
    Read a segment file .s.

    """
    data = np.loadtxt(filename).astype(int)
    assert len(data.shape) == 2
    return data


def _read_function_file(filename):
    """
    Read a function file .f.

    """
    data = np.loadtxt(filename).astype(float)
    assert len(data.shape) == 1
    return data


def read_data_file(filename):
    """
    Generic method to read input file (.s or .f)

    """

    if not os.path.exists(filename):
        raise ValueError(f'Input file "{filename}" not existing!')
    if filename.endswith('.s'):
        return _read_segment_file(filename)
    if filename.endswith('.f'):
        return _read_function_file(filename)

    raise ValueError(f'Input file "{filename}" NOT supported!')


def parse_settings_file(filename):
    """
    Read a generic .json file assumed to contain the input settings.

    """
    with open(filename, 'r', encoding='utf-8') as openfile:
        settings = json.load(openfile)

    return settings
