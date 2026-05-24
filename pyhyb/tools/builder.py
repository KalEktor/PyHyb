# -*- coding: utf-8 -*-
# Copyright (c) 2026, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Hybrid Builder Tools
--------------------
Contains the logic for constructing hybrid structures by combining a macromolecule
(.xyz) with a substrate (.cif) using ASE.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write
from scipy.spatial.distance import cdist


class BuildHybridError(Exception):
    """Base exception for builder failures."""


class InputFileError(BuildHybridError):
    """Raised when input files are missing or invalid."""


class StructureError(BuildHybridError):
    """Raised when a structure cannot be combined safely."""


logger = logging.getLogger("pyhyb.builder")


@dataclass
# pylint: disable=too-many-instance-attributes
class HybridConfig:
    """Configuration data for building a hybrid structure."""
    material_path: Path
    substrate_path: Path
    outdir: Path
    prefix: str | None = None
    placement: str = "center"
    distance: float = 3.0
    collision_threshold: float = 1.5
    rotation: list[float] | None = None
    optimize: bool = False

    def __post_init__(self) -> None:
        """
        Converts string path representations to pathlib.Path objects after initialization.
        """
        self.material_path = Path(self.material_path)
        self.substrate_path = Path(self.substrate_path)
        self.outdir = Path(self.outdir)


class HybridBuilder:
    """
    Constructs a hybrid structure by combining a macromolecule and a substrate.
    Encapsulates validation, reading, placement logic, combination, and writing.
    """

    def __init__(self, config: HybridConfig) -> None:
        """
        Initializes the HybridBuilder with the provided configuration and validates inputs.

        Args:
            config: A HybridConfig instance containing the build parameters.
        """
        self.config = config
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """
        Validates the existence and extensions of the input files, and ensures
        the output directory exists. Raises InputFileError if validation fails.
        """
        if self.config.material_path.suffix.lower() != ".xyz":
            raise InputFileError(
                f"Material file must be .xyz, got: {self.config.material_path.suffix}"
            )
        if self.config.substrate_path.suffix.lower() != ".cif":
            raise InputFileError(
                f"Substrate file must be .cif, got: {self.config.substrate_path.suffix}"
            )

        if not self.config.material_path.is_file():
            raise InputFileError(
                f"Material file not found: {self.config.material_path.resolve()}"
            )
        if not self.config.substrate_path.is_file():
            raise InputFileError(
                f"Substrate file not found: {self.config.substrate_path.resolve()}"
            )

        self.config.outdir.mkdir(parents=True, exist_ok=True)

    def _read_structures(self) -> tuple[Atoms, Atoms]:
        """
        Reads the material and substrate structures from their respective files using ASE.

        Returns:
            A tuple containing the material and substrate Atoms objects.

        Raises:
            StructureError: If either structure is empty or if the substrate lacks
                a valid 3D unit cell.
        """
        logger.info("Reading input structures...")
        material = read(self.config.material_path)
        substrate = read(self.config.substrate_path)

        if len(material) == 0:
            raise StructureError("The material structure is empty.")
        if len(substrate) == 0:
            raise StructureError("The substrate structure is empty.")

        if substrate.cell.rank < 3 or abs(substrate.cell.volume) < 1e-8:
            raise StructureError(
                "The substrate does not appear to have a valid 3D unit cell. "
                "A .cif substrate with a proper cell is required."
            )

        return material, substrate

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def _place_material(self, material: Atoms, substrate: Atoms) -> Atoms:
        """
        Calculates shifts, optimally tilts the molecule if it exceeds the unit cell,
        perfectly centers the geometric bounding box in fractional X/Y,
        and applies an iterative Z-push to avoid collisions.
        """
        placed = material.copy()

        # Cucurbituril Detection and Channel Alignment (make perfectly horizontal)
        is_cucurbituril = (
            len(placed) == 84 and
            sum(1 for sym in placed.symbols if sym == 'O') == 14
        )
        if is_cucurbituril:
            logger.info(
                "Cucurbituril detected. Aligning central channel axis to Z-axis "
                "(perfectly horizontal)..."
            )

            # Find oxygen atoms defining the two portals
            o_indices = [i for i, sym in enumerate(placed.symbols) if sym == 'O']
            o_positions = placed.positions[o_indices]

            # Divide the 14 oxygens into two rings based on distance (7 each)
            # Start with the first oxygen, find its 6 nearest oxygen neighbors
            dists_to_first = np.linalg.norm(o_positions - o_positions[0], axis=1)
            nearest_indices = np.argsort(dists_to_first)[:7]

            ring1 = o_positions[nearest_indices]
            # The remaining 7 oxygens form the second ring
            ring2 = np.delete(o_positions, nearest_indices, axis=0)

            # Compute portal centroids
            c_ring1 = ring1.mean(axis=0)
            c_ring2 = ring2.mean(axis=0)

            # Determine which ring is top and bottom based on Z coordinate of their centroids
            if c_ring1[2] < c_ring2[2]:
                c_bottom = c_ring1
                c_top = c_ring2
            else:
                c_bottom = c_ring2
                c_top = c_ring1

            # Compute the channel direction vector
            axis_vector = c_top - c_bottom
            axis_norm = np.linalg.norm(axis_vector)
            if axis_norm > 1e-6:
                axis_vector /= axis_norm

                # Use ASE's built-in rotate to perform a perfect rigid rotation
                placed.rotate(axis_vector, [1.0, 0.0, 0.0], center='COM')
                logger.info(
                    "Cucurbituril central channel axis successfully aligned with "
                    "X-axis (perfectly horizontal) using ASE rigid rotation."
                )

        # Apply user-specified rotation first
        if self.config.rotation:
            rx, ry, rz = self.config.rotation
            placed.rotate(rx, 'x', center='COM')
            placed.rotate(ry, 'y', center='COM')
            placed.rotate(rz, 'z', center='COM')

        def get_xy_span(atoms: Atoms) -> float:
            frac = substrate.cell.scaled_positions(atoms.positions)
            return max(
                frac[:, 0].max() - frac[:, 0].min(),
                frac[:, 1].max() - frac[:, 1].min()
            )

        # Auto-tilting algorithm if molecule is physically larger than cell
        current_span = get_xy_span(placed)
        if current_span > 0.99:
            logger.info(
                "Molecule span (%.2f of cell) exceeds X/Y boundaries. "
                "Attempting auto-tilt to fit...",
                current_span
            )
            best_atoms = placed.copy()
            best_span = current_span

            # 1. Try rotating around Z (in-plane yaw)
            for angle in range(5, 180, 5):
                test_atoms = placed.copy()
                test_atoms.rotate(angle, 'z', center='COM')
                test_span = get_xy_span(test_atoms)
                if test_span < best_span:
                    best_span = test_span
                    best_atoms = test_atoms.copy()
            placed = best_atoms

            # 2. Try tilting around X and Y (out-of-plane pitch/roll) if still exceeding
            if best_span > 0.99:
                logger.info("In-plane rotation insufficient. Tilting out-of-plane...")
                for rx in range(0, 90, 10):
                    for ry in range(0, 90, 10):
                        if rx == 0 and ry == 0:
                            continue
                        test_atoms = placed.copy()
                        test_atoms.rotate(rx, 'x', center='COM')
                        test_atoms.rotate(ry, 'y', center='COM')
                        test_span = get_xy_span(test_atoms)
                        if test_span < best_span:
                            best_span = test_span
                            best_atoms = test_atoms.copy()
                placed = best_atoms

            if best_span > 0.99:
                logger.warning(
                    "Molecule is still too large after tilting (span = %.2f). "
                    "Some atoms will physically escape the unit cell.",
                    best_span
                )
            else:
                logger.info("Successfully tilted molecule. New span: %.2f of cell.", best_span)

        # Fractional Geometric Bounding Box Centering (X/Y)
        frac = substrate.cell.scaled_positions(placed.positions)
        frac_center = 0.5 * (frac.max(axis=0) + frac.min(axis=0))
        shift_frac = np.array([0.5 - frac_center[0], 0.5 - frac_center[1], 0.0])
        shift_cart = shift_frac @ substrate.cell.array
        placed.translate(shift_cart)

        if self.config.placement == "surface":
            # Find substrate atoms within X/Y bounding box of the centered molecule
            placed_x_min, placed_x_max = (
                placed.positions[:, 0].min(),
                placed.positions[:, 0].max()
            )
            placed_y_min, placed_y_max = (
                placed.positions[:, 1].min(),
                placed.positions[:, 1].max()
            )

            padding = 1.5
            vicinity_indices = []
            for idx, pos in enumerate(substrate.positions):
                if (placed_x_min - padding <= pos[0] <= placed_x_max + padding and
                    placed_y_min - padding <= pos[1] <= placed_y_max + padding):
                    vicinity_indices.append(idx)

            if len(vicinity_indices) > 0:
                local_substrate_max_z = max(substrate.positions[vicinity_indices, 2])
            else:
                local_substrate_max_z = (
                    max(substrate.positions[:, 2]) if len(substrate) > 0 else 0.0
                )

            placed_min_z = placed.positions[:, 2].min()
            # Start molecule bottom at target distance above local substrate peak
            shift_z = (local_substrate_max_z + self.config.distance) - placed_min_z
        else:
            placed_z_center = 0.5 * (placed.positions[:, 2].max() + placed.positions[:, 2].min())
            target_z = 0.5 * substrate.cell.array[2][2]
            shift_z = target_z - placed_z_center

        placed.translate([0.0, 0.0, shift_z])

        # Iterative Z-push for Collision Avoidance
        if len(placed) > 0 and len(substrate) > 0:
            while True:
                distances = cdist(placed.positions, substrate.positions)
                min_dist = float(np.min(distances))
                if min_dist >= self.config.collision_threshold:
                    break
                placed.translate([0.0, 0.0, 0.1])

        return placed

    def _combine_structures(self, substrate: Atoms, material: Atoms) -> Atoms:
        """Combines the substrate and the properly positioned material."""
        combined = substrate.copy()
        combined.extend(material)
        combined.set_cell(substrate.cell)
        combined.set_pbc([True, True, False])

        # Dynamic Z-Vacuum Expansion
        max_z = combined.positions[:, 2].max()
        cell_z = combined.cell[2, 2]
        if max_z > cell_z - 5.0:
            logger.info(
                "Molecule exceeds or approaches cell Z-boundary. "
                "Expanding Z-vacuum dynamically..."
            )
            new_z = max_z + 10.0  # 10 Angstroms of vacuum above highest atom
            c_vector = combined.cell[2]
            scale_factor = new_z / c_vector[2]
            combined.cell[2] = c_vector * scale_factor

        # Clean up legacy CIF data from substrate to prevent ASE writing warnings
        combined.info.pop('occupancy', None)

        return combined

    def build(self) -> Atoms:
        """Executes the build process and returns the final hybrid structure."""
        logger.info("Building hybrid structure (placement: %s)...", self.config.placement)
        material, substrate = self._read_structures()

        # Check if the substrate is wrapped across the Z boundary
        # Wrapping is indicated if there are atoms close to both Z=0 and Z=cell_z
        cell_z = substrate.cell[2, 2]
        if cell_z > 0:
            has_bottom = np.any(substrate.positions[:, 2] < 2.0)
            has_top = np.any(substrate.positions[:, 2] > cell_z - 2.0)
            if has_bottom and has_top:
                logger.info(
                    "Substrate Z-wrapping detected across periodic boundaries. "
                    "Unwrapping..."
                )
                substrate.positions[substrate.positions[:, 2] > 0.5 * cell_z, 2] -= cell_z

        logger.info("Wrapping substrate atoms strictly into X/Y cell boundaries...")
        substrate.set_pbc([True, True, False])
        substrate.wrap()

        logger.info(
            "Positioning material and checking for collisions (threshold: %.2f Å)...",
            self.config.collision_threshold
        )
        placed_material = self._place_material(material, substrate)

        return self._combine_structures(substrate, placed_material)

    def _get_output_prefix(self) -> str:
        """
        Determines the prefix for the output filenames.
        Uses the user-provided prefix if available, otherwise defaults to 'hybrid_structure'.
        """
        if self.config.prefix:
            return self.config.prefix
        return "hybrid_structure"

    def write_outputs(self, hybrid: Atoms) -> tuple[Path, Path, Path]:
        """Writes the hybrid structure to .cif, .gen, and .xyz files."""
        prefix = self._get_output_prefix()
        cif_path = self.config.outdir / f"{prefix}.cif"
        gen_path = self.config.outdir / f"{prefix}.gen"
        xyz_path = self.config.outdir / f"{prefix}.xyz"

        logger.info("Writing output files...")
        write(cif_path, hybrid)
        write(gen_path, hybrid, format="gen")
        write(xyz_path, hybrid)

        return cif_path, gen_path, xyz_path
