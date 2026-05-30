# -*- coding: utf-8 -*-
# Copyright (c) 2023, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""Unit tests for PyHyB input/output functions."""
import os
import pathlib
import unittest
from io import StringIO
from unittest.mock import patch

import numpy as np

from pyhyb.inout.inout import (
    save_results,
    parse_settings_file,
    read_data_file,
)
from pyhyb.info import LOGO

TEST_FILES_DIR = pathlib.Path(__file__).parent / 'test_files'


def setUpModule():  # pylint: disable=invalid-name
    """Print the PyHyB ASCII logo."""
    print(LOGO)


class InoutTesting(unittest.TestCase):
    """Unit tests for PyHyB inout effectiveness."""

    def test_inout(self):
        """Write and read a JSON roundtrip."""
        dummy_dict = {
            'ducati': 999,
            'ferrari': 'F40',
        }
        test_path = str(
            TEST_FILES_DIR / 'test.file'
        )

        with patch(
            'sys.stdout', new=StringIO()
        ) as stdout:
            save_results(test_path, dummy_dict)
        self.assertIn(
            'Results saved', stdout.getvalue().strip()
        )

        read_data = parse_settings_file(test_path)
        if os.path.exists(test_path):
            os.remove(test_path)
        self.assertEqual(dummy_dict, read_data)

    def test_segment_file_reader(self):
        """Read segment files."""
        expected_nok = np.array(
            [[100, 200], [150, 250]]
        )
        source_nok = str(
            TEST_FILES_DIR / 'segment_not_ok.s'
        )
        read_nok = read_data_file(source_nok)
        self.assertEqual(
            read_nok.tolist(), expected_nok.tolist()
        )

        expected_ok = np.array(
            [[100, 200], [200, 300]]
        )
        source_ok = str(
            TEST_FILES_DIR / 'segment_ok.s'
        )
        read_ok = read_data_file(source_ok)
        self.assertEqual(
            read_ok.tolist(), expected_ok.tolist()
        )

        missing = str(TEST_FILES_DIR / 'graal.s')
        with self.assertRaises(ValueError) as ctx:
            read_data_file(missing)
        self.assertEqual(
            str(ctx.exception),
            f'Input file "{missing}" not existing!',
        )

        unsupported = str(
            TEST_FILES_DIR / 'file.unicorn'
        )
        with self.assertRaises(ValueError) as ctx:
            read_data_file(unsupported)
        self.assertEqual(
            str(ctx.exception),
            f'Input file "{unsupported}" NOT supported!',
        )

    def test_function_file_reader(self):
        """Read a function file."""
        source = str(TEST_FILES_DIR / 'function.f')
        expected = np.array(
            [25.0, 26.0, 10.0, 11.0]
        )
        read_ok = read_data_file(source)
        self.assertEqual(
            read_ok.tolist(), expected.tolist()
        )


if __name__ == '__main__':
    unittest.main()
