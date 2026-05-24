# -*- coding: utf-8 -*-
# Copyright (c) 2023, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Test in and output functions.

"""
import os
import pathlib
import unittest
from io import StringIO
from unittest.mock import patch
import numpy as np
from pyhyb.inout.inout import save_results, parse_settings_file, read_data_file

from pyhyb.info import LOGO

TEST_FILES_DIR = pathlib.Path(__file__).parent / 'test_files'


def setUpModule():  # pylint: disable=invalid-name
    """Prints the PyHyB ASCII logo upon loading the test suite."""
    print(LOGO)




class InoutTesting(unittest.TestCase):
    """
    Unit tests to check PyHyB inout effectiveness.

    """
    def test_inout(self):
        """
        Write and read a json.

        """
        dummy_dict = {'ducati': 999,
                      'ferrari': 'F40'}
        test_file_path = str(TEST_FILES_DIR / 'test.file')

        with patch('sys.stdout', new=StringIO()) as stdout:
            save_results(test_file_path, dummy_dict)
        self.assertIn('Results saved', stdout.getvalue().strip())

        read_data = parse_settings_file(test_file_path)
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        self.assertEqual(dummy_dict, read_data)

    def test_segment_file_reader(self):
        """
        Read a segment file.

        """
        expected_read_not_ok = np.array([[100, 200], [150, 250]])
        source_file_not_ok = str(TEST_FILES_DIR / 'segment_not_ok.s')
        read_not_ok = read_data_file(source_file_not_ok)

        self.assertEqual(read_not_ok.tolist(), expected_read_not_ok.tolist())

        expected_read_ok = np.array([[100, 200], [200, 300]])
        source_file_ok = str(TEST_FILES_DIR / 'segment_ok.s')
        read_ok = read_data_file(source_file_ok)

        self.assertEqual(read_ok.tolist(), expected_read_ok.tolist())

        not_existing_file = str(TEST_FILES_DIR / 'graal.s')
        with self.assertRaises(ValueError) as cmess:
            read_data_file(not_existing_file)
        self.assertEqual(str(cmess.exception),
                         f'Input file "{not_existing_file}" not existing!')

        not_supported_file = str(TEST_FILES_DIR / 'file.unicorn')
        with self.assertRaises(ValueError) as cmess:
            read_data_file(not_supported_file)
        self.assertEqual(str(cmess.exception),
                         f'Input file "{not_supported_file}" NOT supported!')

    def test_function_file_reader(self):
        """
        Read a function file.

        """
        source_file = str(TEST_FILES_DIR / 'function.f')
        expected_read = np.array([25.0, 26.0, 10.0, 11.0])
        read_ok = read_data_file(source_file)

        self.assertEqual(read_ok.tolist(), expected_read.tolist())


if __name__ == '__main__':
    unittest.main()
