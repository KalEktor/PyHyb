# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Program Callable

"""
import argparse
import datetime
import sys
from pydec.core.main import pydec_main
from pydec.info import PROGRAM_NAME, LOGO

_DATE_FMT = '%d.%m.%Y %H:%M:%S'


def hello_world():
    """
    Greets.

    """
    timestart = datetime.datetime.now().strftime(_DATE_FMT)
    pyversion = sys.version.split()[0]
    print('\n'.join([LOGO]))
    print(f'Start of execution: {timestart}')
    print(f'Python version: {pyversion}')


def parse_input_file():  # pragma: no cover
    """
    Reads main file.

    """
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument('-i', '--input',
                        help=f'Location of {PROGRAM_NAME} input file',
                        required=False, default=None)
    args_dict = vars(parser.parse_args())
    input_file = args_dict['input']

    return input_file


def bye_world():
    """
    Greets.

    """
    timeend = datetime.datetime.now().strftime(_DATE_FMT)
    print(f'End of {PROGRAM_NAME} execution: {timeend}')


def entry_point():  # pragma: no cover
    """
    Connects executable to main program.

    """
    hello_world()
    input_file = parse_input_file()
    if input_file:
        pydec_main(input_file)
    bye_world()


if __name__ == '__main__':   # pragma: no cover
    entry_point()
