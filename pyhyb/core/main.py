# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Main function.

"""
from pyhyb.core.runner import Geni
from pyhyb.inout.inout import save_results


def pyhyb_main(input_file=None):
    """
    Run the computations.

    """
    run = Geni(input_file)
    run.read_settings()
    run.check_settings()
    run.read_data_files()
    run.check_data()
    results = run.execute()
    run.cheers()
    save_results('results.pydec', results)
