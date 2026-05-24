# -*- coding: utf-8 -*-
# Copyright (c) 2023, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Test program operational functions for single and cross segments or functions.

"""
import unittest
import numpy as np
from pydec.inout.inout import read_data_file
from pydec.tools.tools import check_segment_consistency, local_mean
from pydec.tools.cross_tools import segment_overlap, person, vanilla_person


class ToolsTesting(unittest.TestCase):
    """
    Class for testing program operational functions.

    """
    def test_segment_consistency(self):
        """
        Test read segment consistency.

        """
        source_file_not_ok = 'test_files/segment_not_ok.s'
        source_file_ok = 'test_files/segment_ok.s'
        read_not_ok = read_data_file(source_file_not_ok)
        read_ok = read_data_file(source_file_ok)

        self.assertFalse(check_segment_consistency(read_not_ok))
        self.assertTrue(check_segment_consistency(read_ok))

    def test_segment_overlap(self):
        """
        Test overal between segments.

        """
        segment_1 = np.array([[1, 2], [3, 6]])
        segment_2 = np.array([[0, 1], [1, 5]])

        overlap = segment_overlap(segment_1, segment_2)
        self.assertEqual(overlap, 3)

    def test_function_pearson_correlation_coefficient(self):
        """
        Test Person correlation coefficient between funcitons.

        """
        function_1 = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
        function_2 = np.array([10.5, 11.5, 12.0, 13.0, 13.5, 15.0, 14.0])

        pearson_correlation = person(function_1, function_2)
        self.assertAlmostEqual(pearson_correlation, 0.9452853, 7)

    def test_vanilla_function_pearson_correlation_coefficient(self):
        """
        Test Person correlation coefficient between funcitons.

        """
        function_1 = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
        function_2 = np.array([10.5, 11.5, 12.0, 13.0, 13.5, 15.0, 14.0])

        pearson_correlation = vanilla_person(function_1, function_2)
        self.assertAlmostEqual(pearson_correlation, 0.9452853, 7)

    def test_segment_mean(self):
        """
        Test segment mean over function values.

        """
        segment = np.array([[1, 2], [3, 6]])
        function = np.array([10.5, 11.5, 12.0, 13.0, 13.5, 15.0, 14.0])

        mean = local_mean(segment, function)
        self.assertEqual(mean, 13.25)


if __name__ == '__main__':
    unittest.main()
