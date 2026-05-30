# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
"""
Test helpers for PyHyB test suite.

Shared factory functions used across test modules to avoid
code duplication.
"""
import numpy as np
from ase import Atoms


def build_mock_cucurbituril() -> Atoms:
    """Build a mock cucurbituril Atoms object.

    Creates an 84-atom structure with 14 O in two rings
    (7 + 7) along Z and 70 random C atoms.

    Returns:
        Atoms: A synthetic cucurbituril-like structure.
    """
    symbols = ['O'] * 14 + ['C'] * 70
    pos = np.zeros((84, 3))
    pos[:7] = [
        [1.0, 0.0, 3.0], [0.5, 0.86, 3.0],
        [-0.5, 0.86, 3.0], [-1.0, 0.0, 3.0],
        [-0.5, -0.86, 3.0], [0.5, -0.86, 3.0],
        [0.0, 0.0, 3.0],
    ]
    pos[7:14] = [
        [1.0, 0.0, -3.0], [0.5, 0.86, -3.0],
        [-0.5, 0.86, -3.0], [-1.0, 0.0, -3.0],
        [-0.5, -0.86, -3.0], [0.5, -0.86, -3.0],
        [0.0, 0.0, -3.0],
    ]
    rng = np.random.default_rng(42)
    pos[14:] = rng.uniform(-2.0, 2.0, size=(70, 3))
    return Atoms(symbols=symbols, positions=pos)
