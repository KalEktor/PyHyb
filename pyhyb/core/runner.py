# -*- coding: utf-8 -*-
# Copyright (c) 2024, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Core runner linking inputs to working functions.

Houses the :class:`Geni` orchestrator and the convenience
function :func:`run_build_hybrid`.
"""
from __future__ import annotations

from typing import Any, Callable

from pyhyb.inout.inout import (
    read_data_file,
    parse_settings_file,
)
from pyhyb.tools.tools import (
    local_mean,
    check_segment_consistency,
)
from pyhyb.tools.cross_tools import (
    pearson,
    segment_overlap,
)
from pyhyb.core.hybrid_runner import HybridWorkflowRunner


def run_build_hybrid(
    material_path: str,
    substrate_path: str,
    **kwargs: Any,
) -> str:
    """Execute the hybrid building process.

    Args:
        material_path: Path to the ``.xyz`` file.
        substrate_path: Path to the ``.cif`` file.
        **kwargs: Forwarded to
            :meth:`HybridWorkflowRunner.run`.

    Returns:
        Success message from the builder.

    Raises:
        ValueError: If the build fails.
    """
    runner = HybridWorkflowRunner()
    success, msg = runner.run(
        material_path, substrate_path, **kwargs
    )
    if not success:
        raise ValueError(
            f"Hybrid builder failed: {msg}"
        )
    return msg


DATA_MAP: dict[str, list[str]] = {
    'local_mean': ['segments', 'functions'],
    'build_hybrid': ['materials', 'substrates'],
}

OPERATE_MAP: dict[str, Callable[..., Any]] = {
    'local_mean': local_mean,
    'build_hybrid': run_build_hybrid,
}

CROSS_DATA_MAP: dict[str, str] = {
    'person': 'functions',
    'overlap': 'segments',
}

CROSS_OPERATE_MAP: dict[str, Callable[..., Any]] = {
    'person': pearson,
    'overlap': segment_overlap,
}


class Geni:
    """Main orchestrator class for PyHyB simulations.

    Reads settings and data files, validates them, and
    dispatches tasks and cross-tasks to the appropriate
    compute functions.
    """

    def __init__(
        self,
        input_file: str | None = None,
        description: str = 'PyHyB simulation',
    ) -> None:
        """Initialise the orchestrator.

        Args:
            input_file: Path to a JSON settings file.
            description: Human-readable run description.
        """
        self.description = description
        self.input_file = input_file
        self.settings: dict[str, Any] = {}
        self.data: dict[str, list[Any]] = {
            'segments': [],
            'functions': [],
            'materials': [],
            'substrates': [],
        }

    def read_settings(self) -> None:
        """Read and parse the JSON settings file."""
        self.settings = parse_settings_file(
            self.input_file
        )

    def read_data_files(self) -> None:
        """Load FUNCTION and SEGMENT files from settings."""
        input_cfg = self.settings.get('Input', {})

        for file_s in input_cfg.get(
            'file_segments', []
        ):
            segments = read_data_file(file_s)
            if check_segment_consistency(segments):
                self.data['segments'].append(segments)
            else:
                raise ValueError(
                    f'Invalid segment file {file_s}'
                )  # pragma: no cover

        for file_f in input_cfg.get(
            'file_functions', []
        ):
            self.data['functions'].append(
                read_data_file(file_f)
            )

        for file_m in input_cfg.get(
            'file_materials', []
        ):
            self.data['materials'].append(file_m)

        for file_sub in input_cfg.get(
            'file_substrates', []
        ):
            self.data['substrates'].append(file_sub)

    def check_data(self) -> None:
        """Validate all loaded segments for consistency."""
        for segment in self.data['segments']:
            check_segment_consistency(segment)

    def check_settings(self) -> None:
        """Validate that all tasks are supported.

        Raises:
            ValueError: If a task name is not recognised.
        """
        for main_task in (
            self.settings['Main']['tasks']
        ):
            if main_task not in OPERATE_MAP:
                raise ValueError(
                    f'Task {main_task} not supported'
                )

        cross_tasks = (
            self.settings['Main']['cross_tasks']
        )
        for main_cross_task in cross_tasks:
            if main_cross_task not in CROSS_OPERATE_MAP:
                raise ValueError(
                    f'Cross-Task {main_cross_task} '
                    f'not supported'
                )

    def execute(self) -> dict[str, list[Any]]:
        """Run all tasks and cross-tasks.

        Returns:
            Mapping of task names to result lists.
        """
        results: dict[str, list[Any]] = {}
        main = self.settings['Main']

        for task, idx_task in zip(
            main.get('tasks', []),
            main.get('idx_tasks', []),
        ):
            results[task] = []
            for idx in idx_task:
                data = [
                    self.data[
                        DATA_MAP[task][0]
                    ][idx],
                    self.data[
                        DATA_MAP[task][1]
                    ][idx],
                ]
                if task == 'build_hybrid':
                    builder_settings = (
                        self.settings.get(
                            'Builder', {}
                        )
                    )
                    results[task].append(
                        OPERATE_MAP[task](
                            data[0], data[1],
                            **builder_settings,
                        )
                    )
                else:
                    results[task].append(
                        OPERATE_MAP[task](*data)
                    )

        for task, idx_task in zip(
            main.get('cross_tasks', []),
            main.get('idx_cross_tasks', []),
        ):
            results[task] = []
            for idx in idx_task:
                data = [
                    self.data[
                        CROSS_DATA_MAP[task]
                    ][idx[0]],
                    self.data[
                        CROSS_DATA_MAP[task]
                    ][idx[1]],
                ]
                results[task].append(
                    CROSS_OPERATE_MAP[task](*data)
                )

        return results

    @staticmethod
    def cheers() -> None:
        """Print a completion message."""
        print('Simulation D-O-N-E !')
