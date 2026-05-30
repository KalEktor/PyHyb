# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Main function for running a full PyHyB simulation.

Orchestrates settings reading, data loading, validation,
execution, and result saving.
"""
from __future__ import annotations

from pyhyb.core.runner import Geni
from pyhyb.inout.inout import save_results


def pyhyb_main(
    input_file: str | None = None,
) -> None:
    """Run the full PyHyB computation pipeline.

    Args:
        input_file: Path to the JSON settings file.
    """
    run = Geni(input_file)
    run.read_settings()
    run.check_settings()
    run.read_data_files()
    run.check_data()
    results = run.execute()
    run.cheers()
    save_results('results.pydec', results)
