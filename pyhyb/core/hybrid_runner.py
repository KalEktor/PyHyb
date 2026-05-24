# -*- coding: utf-8 -*-
# Copyright (c) 2026, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
MOD905 Workflow Runner
----------------------
A robust wrapper module for executing the hybrid structure builder.
It manages paths, logging, validation, and execution.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from pyhyb.tools.builder import HybridBuilder, HybridConfig, BuildHybridError
from pyhyb.tools.optimizer import StructureOptimizer


class WorkflowError(Exception):
    """Base exception for workflow errors."""


class InputValidationError(WorkflowError):
    """Raised when input files fail validation."""


@dataclass
class HybridTask:
    """Represents a single hybrid-building task."""
    material_xyz: Path
    substrate_cif: Path
    output_dir: Path

    def __post_init__(self):
        self.material_xyz = Path(self.material_xyz)
        self.substrate_cif = Path(self.substrate_cif)
        self.output_dir = Path(self.output_dir)


class HybridWorkflowRunner:  # pylint: disable=too-few-public-methods
    """
    Manager class to handle the validation and execution of the build_hybrid script
    directly via Python objects, avoiding subprocess calls.
    """

    def __init__(self, log_level: int = logging.INFO):
        """Setup the runner with the given log level."""
        self._setup_logger(log_level)

    def _setup_logger(self, log_level: int) -> None:
        """Configures a professional class-specific logger."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def _validate_task(self, task: HybridTask) -> None:
        """Ensures input files exist, have correct extensions, and manages outdir."""
        self.logger.debug(
            "Validating inputs: %s & %s",
            task.material_xyz.name,
            task.substrate_cif.name
        )

        if task.material_xyz.suffix.lower() != ".xyz":
            raise InputValidationError(
                f"Material must be .xyz, but got {task.material_xyz.suffix}"
            )
        if task.substrate_cif.suffix.lower() != ".cif":
            raise InputValidationError(
                f"Substrate must be .cif, but got {task.substrate_cif.suffix}"
            )

        if not task.material_xyz.exists():
            raise InputValidationError(
                f"Material file does not exist: {task.material_xyz.absolute()}"
            )
        if not task.substrate_cif.exists():
            raise InputValidationError(
                f"Substrate file does not exist: {task.substrate_cif.absolute()}"
            )

        if not task.output_dir.exists():
            self.logger.info("Output directory missing. Creating: %s", task.output_dir.absolute())
            task.output_dir.mkdir(parents=True, exist_ok=True)

    # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
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
        steps: int = 200
    ) -> Tuple[bool, str]:
        """
        Executes the workflow safely.
        Returns a tuple: (Success Boolean, Output / Error String)
        """
        self.logger.info("Initializing Hybrid Workflow...")
        task = HybridTask(
            material_xyz=material_path,
            substrate_cif=substrate_path,
            output_dir=output_dir
        )

        fh = None
        try:
            self._validate_task(task)

            # Setup file logging to output directory
            fh = logging.FileHandler(task.output_dir / "build.log")
            fh.setLevel(self.logger.level)
            fh.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(fh)

            self.logger.info("Running builder on material: %s", task.material_xyz.name)

            # Use direct imports to avoid subprocess overhead
            config = HybridConfig(
                material_path=task.material_xyz,
                substrate_path=task.substrate_cif,
                outdir=task.output_dir,
                placement=placement,
                distance=distance,
                collision_threshold=collision_threshold,
                rotation=rotation,
                optimize=optimize,
                prefix=prefix
            )

            # Forward the log level to the builder's logger
            builder_logger = logging.getLogger("pyhyb.builder")
            builder_logger.setLevel(self.logger.level)
            if not builder_logger.handlers and self.logger.handlers:
                builder_logger.addHandler(self.logger.handlers[0])

            builder = HybridBuilder(config)
            hybrid = builder.build()

            # 1. Save the PRE-RELAXED structure first
            cif_path_pre, gen_path_pre, xyz_path_pre = builder.write_outputs(hybrid)

            msg = (
                f"Pre-relaxed structure written successfully:\n"
                f"  CIF: {cif_path_pre}\n"
                f"  GEN: {gen_path_pre}\n"
                f"  XYZ: {xyz_path_pre}\n"
                f"  Total atoms: {len(hybrid)}"
            )

            # 2. Geometric Optimization
            if optimize:
                self.logger.info("Triggering Geometric Optimization...")

                # Create a dedicated folder for DFTB output files to keep the main output clean
                dftb_workdir = config.outdir / "dftb_calc"
                opt = StructureOptimizer(fmax=fmax, steps=steps, workdir=dftb_workdir)

                hybrid_opt, initial_energy, final_energy = opt.optimize(hybrid)

                # Append '_opt' to prefix and save the RELAXED structure
                if prefix:
                    config.prefix = f"{prefix}_opt"
                else:
                    config.prefix = "hybrid_structure_opt"
                cif_path_opt, gen_path_opt, xyz_path_opt = builder.write_outputs(hybrid_opt)

                msg += (
                    f"\n\nOptimized structure written successfully:\n"
                    f"  CIF: {cif_path_opt}\n"
                    f"  GEN: {gen_path_opt}\n"
                    f"  XYZ: {xyz_path_opt}\n"
                    f"  Energy Minimized: {(initial_energy - final_energy):.4f} eV\n"
                    f"  DFTB logs saved in: {dftb_workdir}"
                )


            self.logger.info("Builder finished successfully.")
            return True, msg

        except InputValidationError as e:
            self.logger.error("Input Validation Failed: %s", e)
            return False, str(e)

        except BuildHybridError as e:
            self.logger.error("Hybrid Builder Error: %s", e)
            return False, str(e)

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.exception("An unexpected global error occurred during the workflow.")
            return False, str(e)

        finally:
            if fh:
                self.logger.removeHandler(fh)
                fh.close()
