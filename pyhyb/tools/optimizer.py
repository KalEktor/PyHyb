# -*- coding: utf-8 -*-
"""
Structure Optimizer Module
--------------------------
Handles geometry optimization of hybrid configurations using DFTB+ and BFGS in ASE.
"""
import logging
import time
import os
from pathlib import Path
from ase import Atoms
from ase.optimize import BFGS
from ase.calculators.dftb import Dftb

logger = logging.getLogger("pyhyb.optimizer")


class StructureOptimizer:  # pylint: disable=too-few-public-methods
    """
    StructureOptimizer class manages the geometric optimization of
    molecular/substrate hybrid configurations using DFTB+.
    """
    def __init__(self, fmax: float = 0.05, steps: int = 200, workdir: Path | str = "."):
        self.fmax = fmax
        self.steps = steps
        self.workdir = Path(workdir)

    def optimize(self, atoms: Atoms) -> tuple[Atoms, float, float]:
        """
        Geometrically optimizes the structure.
        Currently uses DFTB+ calculator.
        Returns the optimized Atoms object, initial energy, and final energy.
        """
        logger.info("Initializing Geometric Optimization...")

        # Check that Slater-Koster parameter directory is specified via DFTB_PREFIX env var
        dftb_prefix = os.environ.get('DFTB_PREFIX')
        if not dftb_prefix:
            raise RuntimeError(
                "DFTB_PREFIX environment variable is not set.\n"
                "To use the Geometric Optimizer with DFTB+, you must download the appropriate "
                "Slater-Koster parameter files matching your elements from dftb.org and "
                "set the DFTB_PREFIX environment variable.\n"
                "Example:\n"
                "  export DFTB_PREFIX=/path/to/slater-koster-files/skfiles/"
            )

        # Verify that the path exists
        dftb_prefix_path = Path(dftb_prefix)
        if not dftb_prefix_path.exists():
            raise RuntimeError(
                f"The directory specified by DFTB_PREFIX does not exist: "
                f"{dftb_prefix_path.absolute()}\n"
                "Please check your environment variable setting."
            )

        self.workdir.mkdir(parents=True, exist_ok=True)

        # Make a copy so we don't accidentally mutate the original if it fails
        opt_atoms = atoms.copy()

        # Attach calculator, pointing it to the designated workdir for output files
        logger.info("Attaching DFTB+ calculator in directory: %s...", self.workdir)
        # We must explicitly set kpts for periodic boundary conditions (like our substrate cell)
        opt_atoms.calc = Dftb(directory=str(self.workdir), kpts=(1, 1, 1))

        try:
            initial_energy = opt_atoms.get_potential_energy()
            logger.info("Initial Total Energy: %.4f eV", initial_energy)

            # logfile writes the steps, trajectory saves the structures
            logger.info("Running BFGS optimization (fmax=%s, max_steps=%s)...",
                        self.fmax, self.steps)
            start_time = time.time()

            dyn = BFGS(opt_atoms,
                       logfile=str(self.workdir / "bfgs_optimization.log"),
                       trajectory=str(self.workdir / "bfgs_optimization.traj"))
            dyn.run(fmax=self.fmax, steps=self.steps)

            final_energy = opt_atoms.get_potential_energy()
            duration = time.time() - start_time

            logger.info("Optimization finished in %.2f seconds.", duration)
            logger.info("Final Total Energy: %.4f eV", final_energy)
            logger.info("Energy minimized by: %.4f eV", initial_energy - final_energy)

            return opt_atoms, initial_energy, final_energy

        except Exception as e:
            logger.error("Optimization failed: %s", str(e))
            raise
