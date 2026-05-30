# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
PyHyB CLI entry point.

Provides the ``pyhyb`` console script installed via pip.
Supports both JSON-driven simulation mode (``-i``) and
direct hybrid-building mode (``-m`` / ``-s``).
"""
import argparse
import datetime
import logging
from pathlib import Path
import sys

from pyhyb.core.main import pyhyb_main
from pyhyb.core.hybrid_runner import HybridWorkflowRunner
from pyhyb.info import PROGRAM_NAME, LOGO
from pyhyb.tools.builder import HybridConfig

_DATE_FMT = '%d.%m.%Y %H:%M:%S'
_DEFAULTS = HybridConfig.defaults()


def hello_world():
    """Print the startup banner with version and time."""
    timestart = datetime.datetime.now().strftime(_DATE_FMT)
    pyversion = sys.version.split()[0]
    print('\n'.join([LOGO]))
    print(f'Start of execution: {timestart}')
    print(f'Python version: {pyversion}')


def parse_args():  # pragma: no cover
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=PROGRAM_NAME
    )
    parser.add_argument(
        '-i', '--input',
        help=f'Location of {PROGRAM_NAME} input file',
        required=False,
        default=None,
    )
    parser.add_argument(
        '-m', '--material',
        help='Path to material .xyz file',
        required=False,
        default=None,
    )
    parser.add_argument(
        '-s', '--substrate',
        help='Path to substrate .cif file',
        required=False,
        default=None,
    )
    parser.add_argument(
        '-o', '--outdir',
        help='Output directory (defaults to PyHyb/output)',
        required=False,
        default=None,
    )
    parser.add_argument(
        '--placement',
        choices=['center', 'surface'],
        default=_DEFAULTS['placement'],
        help='Placement logic (center or surface)',
    )
    parser.add_argument(
        '--distance',
        type=float,
        default=_DEFAULTS['distance'],
        help='Distance above substrate for surface '
             'placement (Å)',
    )
    parser.add_argument(
        '--collision-threshold',
        type=float,
        default=_DEFAULTS['collision_threshold'],
        help='Minimum allowed distance (Å)',
    )
    parser.add_argument(
        '--rotation',
        type=float,
        nargs=3,
        metavar=('X', 'Y', 'Z'),
        help='Rotation angles around COM (degrees)',
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging',
    )
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='Geometrically optimize using DFTB+',
    )
    return parser.parse_args()


def bye_world():
    """Print the shutdown banner."""
    timeend = datetime.datetime.now().strftime(_DATE_FMT)
    print(f'End of {PROGRAM_NAME} execution: {timeend}')


def entry_point():  # pragma: no cover
    """Connect the console script to the main programme."""
    hello_world()
    args = parse_args()

    if args.input:
        pyhyb_main(args.input)
    elif args.material and args.substrate:
        base_dir = (
            Path(__file__).resolve().parent.parent.parent
        )
        input_dir = base_dir / "input"
        output_dir = base_dir / "output"

        outdir = (
            args.outdir if args.outdir
            else str(output_dir)
        )

        mat_path = Path(args.material)
        sub_path = Path(args.substrate)

        if not mat_path.is_absolute() and not mat_path.exists():
            mat_path = input_dir / mat_path.name
        if not sub_path.is_absolute() and not sub_path.exists():
            sub_path = input_dir / sub_path.name

        log_level = (
            logging.DEBUG if args.verbose
            else logging.INFO
        )
        runner = HybridWorkflowRunner(
            log_level=log_level
        )
        runner.run(
            material_path=str(mat_path),
            substrate_path=str(sub_path),
            output_dir=str(outdir),
            placement=args.placement,
            distance=args.distance,
            collision_threshold=args.collision_threshold,
            rotation=args.rotation,
            optimize=args.optimize,
        )
    else:
        print(
            "Please provide either -i for simulation "
            "or both -m and -s for hybrid building."
        )

    bye_world()


if __name__ == '__main__':   # pragma: no cover
    entry_point()
