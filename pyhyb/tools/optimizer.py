# -*- coding: utf-8 -*-
"""
Structure Optimizer Module.

Handles geometry optimisation of hybrid configurations using
DFTB+ and BFGS in ASE.
"""
import logging
import os
import time
from pathlib import Path

from ase import Atoms
from ase.calculators.dftb import Dftb
from ase.optimize import BFGS

logger = logging.getLogger("pyhyb.optimizer")


class StructureOptimizer:  # pylint: disable=too-few-public-methods
    """Manage geometric optimisation via DFTB+.

    Attributes:
        fmax: Force convergence threshold (eV/Å).
        steps: Maximum number of BFGS iterations.
        workdir: Directory for DFTB+ output files.
    """

    def __init__(
        self,
        fmax: float = 0.05,
        steps: int = 200,
        workdir: Path | str = ".",
    ):
        """Initialise the optimiser.

        Args:
            fmax: Force convergence threshold.
            steps: Maximum BFGS iterations.
            workdir: Working directory for DFTB+ files.
        """
        self.fmax = fmax
        self.steps = steps
        self.workdir = Path(workdir)

    def optimize(
        self, atoms: Atoms
    ) -> tuple[Atoms, float, float]:
        """Geometrically optimise the structure.

        Args:
            atoms: The input structure to optimise.

        Returns:
            A tuple ``(optimised_atoms, E_initial, E_final)``.

        Raises:
            RuntimeError: If ``DFTB_PREFIX`` is unset or the
                path does not exist.
        """
        logger.info("Initializing Geometric Optimization...")

        dftb_prefix = os.environ.get('DFTB_PREFIX')
        if not dftb_prefix:
            raise RuntimeError(
                "DFTB_PREFIX environment variable is not "
                "set.\nTo use the Geometric Optimizer with "
                "DFTB+, you must download the appropriate "
                "Slater-Koster parameter files matching "
                "your elements from dftb.org and set the "
                "DFTB_PREFIX environment variable.\n"
                "Example:\n"
                "  export DFTB_PREFIX="
                "/path/to/slater-koster-files/skfiles/"
            )

        dftb_prefix_path = Path(dftb_prefix)
        if not dftb_prefix_path.exists():
            raise RuntimeError(
                "The directory specified by DFTB_PREFIX "
                "does not exist: "
                f"{dftb_prefix_path.absolute()}\n"
                "Please check your environment variable "
                "setting."
            )

        self.workdir.mkdir(parents=True, exist_ok=True)
        opt_atoms = atoms.copy()

        logger.info(
            "Attaching DFTB+ calculator in directory: "
            "%s...",
            self.workdir,
        )
        opt_atoms.calc = Dftb(
            directory=str(self.workdir), kpts=(1, 1, 1)
        )

        try:
            initial_energy = (
                opt_atoms.get_potential_energy()
            )
            logger.info(
                "Initial Total Energy: %.4f eV",
                initial_energy,
            )

            logger.info(
                "Running BFGS optimization "
                "(fmax=%s, max_steps=%s)...",
                self.fmax,
                self.steps,
            )
            start_time = time.time()

            log_path = str(
                self.workdir / "bfgs_optimization.log"
            )
            traj_path = str(
                self.workdir / "bfgs_optimization.traj"
            )
            dyn = BFGS(
                opt_atoms,
                logfile=log_path,
                trajectory=traj_path,
            )
            dyn.run(fmax=self.fmax, steps=self.steps)

            final_energy = (
                opt_atoms.get_potential_energy()
            )
            duration = time.time() - start_time

            logger.info(
                "Optimization finished in %.2f seconds.",
                duration,
            )
            logger.info(
                "Final Total Energy: %.4f eV",
                final_energy,
            )
            logger.info(
                "Energy minimized by: %.4f eV",
                initial_energy - final_energy,
            )

            return opt_atoms, initial_energy, final_energy

        except Exception as exc:
            logger.error(
                "Optimization failed: %s", str(exc)
            )
            raise
