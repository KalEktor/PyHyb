# -*- coding: utf-8 -*-
# Copyright (c) 2023, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Test program structure.

"""
import os
import pathlib
import unittest
from io import StringIO
from unittest.mock import patch
from pyhyb.core.runner import Geni
from pyhyb.core.main import pyhyb_main
from pyhyb.bin.pyhybrun import hello_world, bye_world

TEST_FILES_DIR = pathlib.Path(__file__).parent / 'test_files'


class StructureTesting(unittest.TestCase):
    """
    Class for testing program structure.

    """
    def test_main(self):
        """
        Test main runner function.

        """
        general = Geni()
        general.settings['Main'] = {'tasks': ['gnegne']}
        with self.assertRaises(ValueError) as smess:
            general.check_settings()
        self.assertIn('Task', str(smess.exception))

        general = Geni()
        general.settings['Main'] = {'tasks': [],
                                    'cross_tasks': ['nanna']}
        with self.assertRaises(ValueError) as smess:
            general.check_settings()
        self.assertIn('Cross-Task', str(smess.exception))

        with patch('sys.stdout', new=StringIO()) as stdout:
            general.cheers()
        self.assertIn('D-O-N-E', stdout.getvalue().strip())

    def test_pyhyb_main(self):
        """
        Test main function.

        """
        old_cwd = os.getcwd()
        os.chdir(str(TEST_FILES_DIR.parent))
        try:
            with patch('sys.stdout', new=StringIO()) as stdout:
                pyhyb_main(input_file='test_files/test.json')
            self.assertIn('D-O-N-E', stdout.getvalue().strip())
        finally:
            os.chdir(old_cwd)

    def test_polite_functions(self):
        """
        Test greeting function.

        """
        with patch('sys.stdout', new=StringIO()) as stdout:
            hello_world()
        self.assertIn('rid', stdout.getvalue().strip())
        with patch('sys.stdout', new=StringIO()) as stdout:
            bye_world()
        self.assertIn('execution', stdout.getvalue().strip())


if __name__ == '__main__':
    unittest.main()
