# -*- coding: utf-8 -*-
# Copyright (c) 2023, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Unit tests for single-segment and cross-segment functions.
"""
import pathlib
import unittest
import warnings

import numpy as np

from pyhyb.inout.inout import read_data_file
from pyhyb.tools.tools import (
    check_segment_consistency,
    local_mean,
)
from pyhyb.tools.cross_tools import (
    segment_overlap,
    pearson,
    vanilla_pearson,
    person,
    vanilla_person,
)

TEST_FILES_DIR = (
    pathlib.Path(__file__).parent / 'test_files'
)


class ToolsTesting(unittest.TestCase):
    """Tests for segment and function tools."""

    def test_segment_consistency(self):
        """Test read segment consistency."""
        source_nok = str(
            TEST_FILES_DIR / 'segment_not_ok.s'
        )
        source_ok = str(
            TEST_FILES_DIR / 'segment_ok.s'
        )
        read_nok = read_data_file(source_nok)
        read_ok = read_data_file(source_ok)

        self.assertFalse(
            check_segment_consistency(read_nok)
        )
        self.assertTrue(
            check_segment_consistency(read_ok)
        )

    def test_segment_overlap(self):
        """Test overlap between segments."""
        seg_1 = np.array([[1, 2], [3, 6]])
        seg_2 = np.array([[0, 1], [1, 5]])

        overlap = segment_overlap(seg_1, seg_2)
        self.assertEqual(overlap, 3)

    def test_pearson_correlation(self):
        """Test Pearson correlation coefficient."""
        f1 = np.array([
            10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0
        ])
        f2 = np.array([
            10.5, 11.5, 12.0, 13.0, 13.5, 15.0, 14.0
        ])

        corr = pearson(f1, f2)
        self.assertAlmostEqual(corr, 0.9452853, 7)

    def test_vanilla_pearson_correlation(self):
        """Test vanilla Pearson correlation."""
        f1 = np.array([
            10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0
        ])
        f2 = np.array([
            10.5, 11.5, 12.0, 13.0, 13.5, 15.0, 14.0
        ])

        corr = vanilla_pearson(f1, f2)
        self.assertAlmostEqual(corr, 0.9452853, 7)

    def test_deprecated_person_alias(self):
        """Deprecated person() emits a warning."""
        f1 = np.array([1.0, 2.0, 3.0])
        f2 = np.array([1.0, 2.0, 3.0])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = person(f1, f2)
            self.assertEqual(len(w), 1)
            self.assertIn(
                "deprecated", str(w[0].message)
            )
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_deprecated_vanilla_person_alias(self):
        """Deprecated vanilla_person() emits warning."""
        f1 = np.array([1.0, 2.0, 3.0])
        f2 = np.array([1.0, 2.0, 3.0])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = vanilla_person(f1, f2)
            self.assertEqual(len(w), 1)
            self.assertIn(
                "deprecated", str(w[0].message)
            )
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_segment_mean(self):
        """Test segment mean over function values."""
        seg = np.array([[1, 2], [3, 6]])
        func = np.array([
            10.5, 11.5, 12.0, 13.0, 13.5, 15.0, 14.0
        ])

        mean = local_mean(seg, func)
        self.assertEqual(mean, 13.25)


if __name__ == '__main__':
    unittest.main()
