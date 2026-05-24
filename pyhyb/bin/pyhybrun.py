# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Program Callable

"""
import argparse
import datetime
import logging
from pathlib import Path
import sys
from pyhyb.core.main import pyhyb_main
from pyhyb.core.hybrid_runner import HybridWorkflowRunner
from pyhyb.info import PROGRAM_NAME, LOGO

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


def parse_args():  # pragma: no cover
    """
    Reads arguments.

    """
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument('-i', '--input',
                        help=f'Location of {PROGRAM_NAME} input file',
                        required=False, default=None)
    parser.add_argument('-f', '--fuckers',
                        help='Randomly insult a user',
                        required=False, default='Fuck off')
    parser.add_argument('-m', '--material',
                        help='Path to material .xyz file for building hybrid structure',
                        required=False, default=None)
    parser.add_argument('-s', '--substrate',
                        help='Path to substrate .cif file for building hybrid structure',
                        required=False, default=None)
    parser.add_argument('-o', '--outdir',
                        help='Output directory (defaults to PyHyb/output)',
                        required=False, default=None)
    parser.add_argument('--placement',
                        choices=['center', 'surface'],
                        default='center',
                        help='Placement logic (center or surface)')
    parser.add_argument('--distance',
                        type=float,
                        default=3.0,
                        help='Distance above substrate for surface placement')
    parser.add_argument('--collision-threshold',
                        type=float,
                        default=1.5,
                        help='Minimum allowed distance (Å) to detect collisions')
    parser.add_argument('--rotation',
                        type=float,
                        nargs=3,
                        metavar=('X', 'Y', 'Z'),
                        help='Rotation angles around center of mass (degrees) for X, Y, and Z')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--optimize',
                        action='store_true',
                        help='Geometrically optimize the final structure using DFT placeholder')
    return parser.parse_args()


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
    args = parse_args()

    if args.input:
        pyhyb_main(args.input)
    elif args.material and args.substrate:
        # Setup paths relative to the package root
        base_dir = Path(__file__).resolve().parent.parent.parent
        input_dir = base_dir / "input"
        output_dir = base_dir / "output"

        outdir = args.outdir if args.outdir else str(output_dir)

        # Check if the inputs are files in the input folder
        mat_path = Path(args.material)
        sub_path = Path(args.substrate)

        if not mat_path.is_absolute() and not mat_path.exists():
            mat_path = input_dir / mat_path.name
        if not sub_path.is_absolute() and not sub_path.exists():
            sub_path = input_dir / sub_path.name

        log_level = logging.DEBUG if args.verbose else logging.INFO
        runner = HybridWorkflowRunner(log_level=log_level)
        runner.run(
            material_path=str(mat_path),
            substrate_path=str(sub_path),
            output_dir=str(outdir),
            placement=args.placement,
            distance=args.distance,
            collision_threshold=args.collision_threshold,
            rotation=args.rotation,
            optimize=args.optimize
        )
    else:
        print("Please provide either -i for simulation or both -m and -s for hybrid building.")

    bye_world()


if __name__ == '__main__':   # pragma: no cover
    entry_point()
