# -*- coding: utf-8 -*-
# Copyright (c) 2026, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Hybrid Workflow Runner.

A robust wrapper module for executing the hybrid structure
builder.  It manages paths, logging, validation, and execution.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from pyhyb.tools.builder import (
    BuildHybridError,
    HybridBuilder,
    HybridConfig,
)
from pyhyb.tools.optimizer import StructureOptimizer


class WorkflowError(Exception):
    """Base exception for workflow errors."""


class InputValidationError(WorkflowError):
    """Raised when input files fail validation."""


@dataclass
class HybridTask:
    """Represent a single hybrid-building task.

    Attributes:
        material_xyz: Path to the macromolecule file.
        substrate_cif: Path to the substrate file.
        output_dir: Path to the output directory.
    """

    material_xyz: Path
    substrate_cif: Path
    output_dir: Path

    def __post_init__(self):
        """Convert strings to :class:`pathlib.Path`."""
        self.material_xyz = Path(self.material_xyz)
        self.substrate_cif = Path(self.substrate_cif)
        self.output_dir = Path(self.output_dir)


# pylint: disable=too-few-public-methods
class HybridWorkflowRunner:
    """Validate and execute the hybrid build workflow.

    Avoids subprocess calls by importing the builder directly.
    """

    def __init__(
        self, log_level: int = logging.INFO
    ):
        """Set up the runner with the given log level.

        Args:
            log_level: Python logging level constant.
        """
        self._setup_logger(log_level)

    def _setup_logger(self, log_level: int) -> None:
        """Configure a class-specific logger.

        Args:
            log_level: Python logging level constant.
        """
        self.logger = logging.getLogger(
            self.__class__.__name__
        )
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - '
                '%(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _validate_task(self, task: HybridTask) -> None:
        """Ensure inputs exist and have correct extensions.

        Args:
            task: The task to validate.

        Raises:
            InputValidationError: On bad extensions or
                missing files.
        """
        self.logger.debug(
            "Validating inputs: %s & %s",
            task.material_xyz.name,
            task.substrate_cif.name,
        )

        if task.material_xyz.suffix.lower() != ".xyz":
            raise InputValidationError(
                "Material must be .xyz, but got "
                f"{task.material_xyz.suffix}"
            )
        if task.substrate_cif.suffix.lower() != ".cif":
            raise InputValidationError(
                "Substrate must be .cif, but got "
                f"{task.substrate_cif.suffix}"
            )

        if not task.material_xyz.exists():
            raise InputValidationError(
                "Material file does not exist: "
                f"{task.material_xyz.absolute()}"
            )
        if not task.substrate_cif.exists():
            raise InputValidationError(
                "Substrate file does not exist: "
                f"{task.substrate_cif.absolute()}"
            )

        if not task.output_dir.exists():
            self.logger.info(
                "Output directory missing. Creating: %s",
                task.output_dir.absolute(),
            )
            task.output_dir.mkdir(
                parents=True, exist_ok=True
            )

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-positional-arguments
    def run(
        self,
        material_path: str,
        substrate_path: str,
        output_dir: str = ".",
        placement: str = "center",
        distance: float = 3.0,
        collision_threshold: float = 1.5,
        rotation: list[float] | None = None,
        optimize: bool = False,
        prefix: str | None = None,
        fmax: float = 0.05,
        steps: int = 200,
    ) -> Tuple[bool, str]:
        """Execute the workflow safely.

        Args:
            material_path: Path to the ``.xyz`` file.
            substrate_path: Path to the ``.cif`` file.
            output_dir: Where to write outputs.
            placement: ``'center'`` or ``'surface'``.
            distance: Starting height in Å.
            collision_threshold: Min distance in Å.
            rotation: Optional Euler angles ``[rx, ry, rz]``.
            optimize: Run DFTB+ relaxation.
            prefix: Output filename prefix.
            fmax: Force convergence for BFGS.
            steps: Max BFGS iterations.

        Returns:
            A tuple ``(success, message)``.
        """
        self.logger.info(
            "Initializing Hybrid Workflow..."
        )
        task = HybridTask(
            material_xyz=material_path,
            substrate_cif=substrate_path,
            output_dir=output_dir,
        )

        file_handler = None
        try:
            self._validate_task(task)

            # File logging into output directory
            file_handler = logging.FileHandler(
                task.output_dir / "build.log"
            )
            file_handler.setLevel(self.logger.level)
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - '
                    '%(levelname)s - %(message)s'
                )
            )
            self.logger.addHandler(file_handler)

            self.logger.info(
                "Running builder on material: %s",
                task.material_xyz.name,
            )

            config = HybridConfig(
                material_path=task.material_xyz,
                substrate_path=task.substrate_cif,
                outdir=task.output_dir,
                placement=placement,
                distance=distance,
                collision_threshold=collision_threshold,
                rotation=rotation,
                optimize=optimize,
                prefix=prefix,
            )

            # Forward log level to builder logger
            builder_logger = logging.getLogger(
                "pyhyb.builder"
            )
            builder_logger.setLevel(self.logger.level)
            if (
                not builder_logger.handlers
                and self.logger.handlers
            ):
                builder_logger.addHandler(
                    self.logger.handlers[0]
                )

            builder = HybridBuilder(config)
            hybrid = builder.build()

            # Write pre-relaxed outputs
            cif_pre, gen_pre, xyz_pre = (
                builder.write_outputs(hybrid)
            )

            # Write provenance manifest
            builder.write_manifest(hybrid)

            msg = (
                "Pre-relaxed structure written "
                "successfully:\n"
                f"  CIF: {cif_pre}\n"
                f"  GEN: {gen_pre}\n"
                f"  XYZ: {xyz_pre}\n"
                f"  Total atoms: {len(hybrid)}"
            )

            # Geometric optimisation
            if optimize:
                msg += self._run_optimisation(
                    config, builder, hybrid,
                    prefix, fmax, steps,
                )

            self.logger.info(
                "Builder finished successfully."
            )
            return True, msg

        except InputValidationError as exc:
            self.logger.error(
                "Input Validation Failed: %s", exc
            )
            return False, str(exc)

        except BuildHybridError as exc:
            self.logger.error(
                "Hybrid Builder Error: %s", exc
            )
            return False, str(exc)

        # pylint: disable=broad-exception-caught
        except Exception as exc:
            self.logger.exception(
                "An unexpected global error occurred "
                "during the workflow."
            )
            return False, str(exc)

        finally:
            if file_handler:
                self.logger.removeHandler(file_handler)
                file_handler.close()

    @staticmethod
    def _run_optimisation(
        config, builder, hybrid, prefix, fmax, steps
    ):
        """Run DFTB+ optimisation and save outputs.

        Args:
            config: The build config.
            builder: The HybridBuilder instance.
            hybrid: The pre-relaxed structure.
            prefix: Output filename prefix.
            fmax: Force convergence.
            steps: Max BFGS iterations.

        Returns:
            str: Additional message text.
        """
        dftb_workdir = config.outdir / "dftb_calc"
        opt = StructureOptimizer(
            fmax=fmax, steps=steps, workdir=dftb_workdir
        )

        hybrid_opt, initial_e, final_e = opt.optimize(
            hybrid
        )

        if prefix:
            config.prefix = f"{prefix}_opt"
        else:
            config.prefix = "hybrid_structure_opt"

        cif_opt, gen_opt, xyz_opt = (
            builder.write_outputs(hybrid_opt)
        )
        builder.write_manifest(hybrid_opt)

        delta = initial_e - final_e
        return (
            "\n\nOptimized structure written "
            "successfully:\n"
            f"  CIF: {cif_opt}\n"
            f"  GEN: {gen_opt}\n"
            f"  XYZ: {xyz_opt}\n"
            f"  Energy Minimized: {delta:.4f} eV\n"
            f"  DFTB logs saved in: {dftb_workdir}"
        )
