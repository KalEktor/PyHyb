# -*- coding: utf-8 -*-
# Copyright (c) 2026, Enrico Development Team.
# Distributed under the LGPLv2.1+ License.
"""
Hybrid Builder Tools.

Contains the logic for constructing hybrid structures by
combining a macromolecule (.xyz) with a substrate (.cif) using
ASE.  The central class is :class:`HybridBuilder`, which owns
the full build-state lifecycle: validation → reading → placement
→ combination → writing.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write
from scipy.spatial.distance import cdist


class _BuildLog:
    """In-memory log handler for capturing build decisions.

    Attaches to the builder logger during a build and stores
    each message as a string.  The captured entries are later
    written into the build manifest so that algorithmic
    decisions are available offline.

    Usage::

        log = _BuildLog()
        log.attach()
        # ... build ...
        log.detach()
        entries = log.entries   # list[str]
    """

    def __init__(self) -> None:
        self.entries: list[str] = []
        self._handler = logging.Handler()
        self._handler.emit = self._emit  # type: ignore[assignment]
        self._handler.setLevel(logging.DEBUG)
        self._prev_level: int | None = None

    def _emit(self, record: logging.LogRecord) -> None:
        """Store formatted log record."""
        self.entries.append(
            self._handler.format(record)
        )

    def attach(self) -> None:
        """Attach handler to the builder logger.

        Ensures the logger level is at least INFO so
        that build-decision messages pass through.
        """
        self._prev_level = logger.level
        if logger.level > logging.INFO or logger.level == 0:
            logger.setLevel(logging.INFO)
        logger.addHandler(self._handler)

    def detach(self) -> None:
        """Detach handler and restore previous log level."""
        logger.removeHandler(self._handler)
        if self._prev_level is not None:
            logger.setLevel(self._prev_level)


class BuildHybridError(Exception):
    """Base exception for builder failures."""


class InputFileError(BuildHybridError):
    """Raised when input files are missing or invalid."""


class StructureError(BuildHybridError):
    """Raised when a structure cannot be combined safely."""


logger = logging.getLogger("pyhyb.builder")


# Default values used across CLI, GUI, and programmatic API.
_DEFAULTS = {
    "placement": "center",
    "distance": 3.0,
    "collision_threshold": 1.5,
    "rotation": None,
    "optimize": False,
}


@dataclass
# pylint: disable=too-many-instance-attributes
class HybridConfig:
    """Configuration data for building a hybrid structure.

    Attributes:
        material_path: Path to the macromolecule ``.xyz`` file.
        substrate_path: Path to the periodic substrate ``.cif``
            file.
        outdir: Directory where output files will be written.
        prefix: Optional filename prefix for outputs.
        placement: Vertical positioning logic (``center`` or
            ``surface``).
        distance: Starting height above the substrate surface
            in Ångströms.
        collision_threshold: Minimum allowed inter-atomic
            distance in Ångströms.
        rotation: Optional Euler rotation angles ``[rx, ry, rz]``
            in degrees.
        optimize: Whether to run DFTB+ geometry optimisation.
    """

    material_path: Path
    substrate_path: Path
    outdir: Path
    prefix: str | None = None
    placement: str = _DEFAULTS["placement"]
    distance: float = _DEFAULTS["distance"]
    collision_threshold: float = _DEFAULTS["collision_threshold"]
    rotation: list[float] | None = _DEFAULTS["rotation"]
    optimize: bool = _DEFAULTS["optimize"]

    def __post_init__(self) -> None:
        """Convert string paths to :class:`pathlib.Path` objects."""
        self.material_path = Path(self.material_path)
        self.substrate_path = Path(self.substrate_path)
        self.outdir = Path(self.outdir)

    # ----------------------------------------------------------
    # Single source of truth for parameter defaults
    # ----------------------------------------------------------
    @classmethod
    def defaults(cls) -> dict:
        """Return a dict of default parameter values.

        Both the CLI argument parsers and the Streamlit GUI
        should pull their defaults from this method so that
        changes propagate from a single location.

        Returns:
            dict: Mapping of parameter name to default value.
        """
        return dict(_DEFAULTS)


class HybridBuilder:
    """Construct a hybrid structure.

    Combines a macromolecule and a substrate by encapsulating
    validation, reading, placement logic, combination, and
    output writing.
    """

    def __init__(self, config: HybridConfig) -> None:
        """Initialise the builder with *config* and validate.

        Args:
            config: A :class:`HybridConfig` instance containing
                the build parameters.
        """
        self.config = config
        self._build_log = _BuildLog()
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Check input file extensions, existence, and outdir.

        Raises:
            InputFileError: If files are missing or have wrong
                extensions.
        """
        if self.config.material_path.suffix.lower() != ".xyz":
            raise InputFileError(
                "Material file must be .xyz, got: "
                f"{self.config.material_path.suffix}"
            )
        if self.config.substrate_path.suffix.lower() != ".cif":
            raise InputFileError(
                "Substrate file must be .cif, got: "
                f"{self.config.substrate_path.suffix}"
            )

        if not self.config.material_path.is_file():
            raise InputFileError(
                "Material file not found: "
                f"{self.config.material_path.resolve()}"
            )
        if not self.config.substrate_path.is_file():
            raise InputFileError(
                "Substrate file not found: "
                f"{self.config.substrate_path.resolve()}"
            )

        self.config.outdir.mkdir(parents=True, exist_ok=True)

    def _read_structures(self) -> tuple[Atoms, Atoms]:
        """Read material and substrate via ASE.

        Returns:
            A tuple ``(material, substrate)`` of ASE
            :class:`~ase.Atoms` objects.

        Raises:
            StructureError: If either structure is empty or the
                substrate lacks a valid 3-D unit cell.
        """
        logger.info("Reading input structures...")
        material = read(self.config.material_path)
        substrate = read(self.config.substrate_path)

        if len(material) == 0:
            raise StructureError(
                "The material structure is empty."
            )
        if len(substrate) == 0:
            raise StructureError(
                "The substrate structure is empty."
            )

        cell_ok = (
            substrate.cell.rank >= 3
            and abs(substrate.cell.volume) >= 1e-8
        )
        if not cell_ok:
            raise StructureError(
                "The substrate does not appear to have a valid "
                "3D unit cell. A .cif substrate with a proper "
                "cell is required."
            )

        return material, substrate

    # pylint: disable=too-many-locals,too-many-branches
    # pylint: disable=too-many-statements
    def _place_material(
        self, material: Atoms, substrate: Atoms
    ) -> Atoms:
        """Position the molecule on the substrate.

        Calculates shifts, optimally tilts the molecule if it
        exceeds the unit cell, perfectly centres the geometric
        bounding box in fractional X/Y, and applies an iterative
        Z-push to avoid collisions.

        Args:
            material: The macromolecule to place.
            substrate: The periodic substrate.

        Returns:
            A copy of *material* translated/rotated into its
            final position.
        """
        placed = material.copy()

        # --- Cucurbituril channel alignment ---------------
        is_cucurbituril = (
            len(placed) == 84
            and sum(
                1 for sym in placed.symbols if sym == 'O'
            ) == 14
        )
        if is_cucurbituril:
            logger.info(
                "Cucurbituril detected. Aligning central "
                "channel axis to Z-axis (perfectly "
                "horizontal)..."
            )
            placed = self._align_cucurbituril(placed)

        # --- User-specified rotation ----------------------
        if self.config.rotation:
            rx, ry, rz = self.config.rotation
            logger.info(
                "Applying user Euler rotation: "
                "rx=%.1f°, ry=%.1f°, rz=%.1f°",
                rx, ry, rz,
            )
            placed.rotate(rx, 'x', center='COM')
            placed.rotate(ry, 'y', center='COM')
            placed.rotate(rz, 'z', center='COM')

        # --- Auto-tilting if too wide for the cell --------
        placed = self._auto_tilt(placed, substrate)

        # --- Fractional bounding-box centering (X/Y) ------
        frac = substrate.cell.scaled_positions(
            placed.positions
        )
        frac_center = 0.5 * (
            frac.max(axis=0) + frac.min(axis=0)
        )
        shift_frac = np.array([
            0.5 - frac_center[0],
            0.5 - frac_center[1],
            0.0,
        ])
        shift_cart = shift_frac @ substrate.cell.array
        placed.translate(shift_cart)

        # --- Vertical positioning -------------------------
        shift_z = self._compute_z_shift(placed, substrate)
        placed.translate([0.0, 0.0, shift_z])

        # --- Iterative Z-push for collision avoidance -----
        if len(placed) > 0 and len(substrate) > 0:
            push_count = 0
            while True:
                distances = cdist(
                    placed.positions,
                    substrate.positions,
                )
                min_dist = float(np.min(distances))
                if min_dist >= self.config.collision_threshold:
                    break
                placed.translate([0.0, 0.0, 0.1])
                push_count += 1
            if push_count > 0:
                logger.info(
                    "Collision avoidance: pushed "
                    "molecule +%.1f Å in Z "
                    "(%d × 0.1 Å steps). "
                    "Final min distance: %.2f Å.",
                    push_count * 0.1,
                    push_count,
                    min_dist,
                )
            else:
                logger.info(
                    "No collision detected "
                    "(min distance: %.2f Å ≥ "
                    "threshold %.2f Å).",
                    min_dist,
                    self.config.collision_threshold,
                )

        return placed

    # ----------------------------------------------------------
    # Helper: cucurbituril alignment
    # ----------------------------------------------------------
    @staticmethod
    def _align_cucurbituril(placed: Atoms) -> Atoms:
        """Align a cucurbituril channel axis to the X-axis.

        Args:
            placed: The cucurbituril Atoms object.

        Returns:
            The rotated Atoms object.
        """
        o_indices = [
            i for i, sym in enumerate(placed.symbols)
            if sym == 'O'
        ]
        o_positions = placed.positions[o_indices]

        dists_to_first = np.linalg.norm(
            o_positions - o_positions[0], axis=1
        )
        nearest_indices = np.argsort(dists_to_first)[:7]

        ring1 = o_positions[nearest_indices]
        ring2 = np.delete(o_positions, nearest_indices, axis=0)

        c_ring1 = ring1.mean(axis=0)
        c_ring2 = ring2.mean(axis=0)

        if c_ring1[2] < c_ring2[2]:
            c_bottom, c_top = c_ring1, c_ring2
        else:
            c_bottom, c_top = c_ring2, c_ring1

        axis_vector = c_top - c_bottom
        axis_norm = np.linalg.norm(axis_vector)
        if axis_norm > 1e-6:
            axis_vector /= axis_norm
            placed.rotate(
                axis_vector, [1.0, 0.0, 0.0], center='COM'
            )
            logger.info(
                "Cucurbituril channel axis aligned with "
                "X-axis using ASE rigid rotation."
            )
        return placed

    # ----------------------------------------------------------
    # Helper: auto-tilt
    # ----------------------------------------------------------
    def _auto_tilt(
        self, placed: Atoms, substrate: Atoms
    ) -> Atoms:
        """Rotate the molecule to fit inside the unit cell.

        Tries in-plane yaw first, then out-of-plane pitch/roll.

        Args:
            placed: The molecule to rotate.
            substrate: The substrate (provides the cell).

        Returns:
            Possibly rotated copy of *placed*.
        """

        def get_xy_span(atoms: Atoms) -> float:
            frac = substrate.cell.scaled_positions(
                atoms.positions
            )
            return max(
                frac[:, 0].max() - frac[:, 0].min(),
                frac[:, 1].max() - frac[:, 1].min(),
            )

        current_span = get_xy_span(placed)
        if current_span <= 0.99:
            return placed

        logger.info(
            "Molecule span (%.2f of cell) exceeds X/Y "
            "boundaries. Attempting auto-tilt to fit...",
            current_span,
        )
        best_atoms = placed.copy()
        best_span = current_span

        # 1. In-plane yaw around Z
        for angle in range(5, 180, 5):
            test = placed.copy()
            test.rotate(angle, 'z', center='COM')
            span = get_xy_span(test)
            if span < best_span:
                best_span = span
                best_atoms = test.copy()
        placed = best_atoms

        # 2. Out-of-plane pitch/roll if still too wide
        if best_span > 0.99:
            logger.info(
                "In-plane rotation insufficient. "
                "Tilting out-of-plane..."
            )
            for rx_angle in range(0, 90, 10):
                for ry_angle in range(0, 90, 10):
                    if rx_angle == 0 and ry_angle == 0:
                        continue
                    test = placed.copy()
                    test.rotate(
                        rx_angle, 'x', center='COM'
                    )
                    test.rotate(
                        ry_angle, 'y', center='COM'
                    )
                    span = get_xy_span(test)
                    if span < best_span:
                        best_span = span
                        best_atoms = test.copy()
            placed = best_atoms

        if best_span > 0.99:
            logger.warning(
                "Molecule is still too large after tilting "
                "(span = %.2f). Some atoms will physically "
                "escape the unit cell.",
                best_span,
            )
        else:
            logger.info(
                "Successfully tilted molecule. "
                "New span: %.2f of cell.",
                best_span,
            )
        return placed

    # ----------------------------------------------------------
    # Helper: Z-shift computation
    # ----------------------------------------------------------
    def _compute_z_shift(
        self, placed: Atoms, substrate: Atoms
    ) -> float:
        """Compute the vertical translation for placement.

        Args:
            placed: The centred molecule.
            substrate: The substrate.

        Returns:
            The Z translation in Ångströms.
        """
        if self.config.placement == "surface":
            px_min = placed.positions[:, 0].min()
            px_max = placed.positions[:, 0].max()
            py_min = placed.positions[:, 1].min()
            py_max = placed.positions[:, 1].max()

            padding = 1.5
            vicinity = [
                idx
                for idx, pos in enumerate(substrate.positions)
                if (px_min - padding <= pos[0]
                    <= px_max + padding)
                and (py_min - padding <= pos[1]
                     <= py_max + padding)
            ]

            if vicinity:
                local_z = max(
                    substrate.positions[vicinity, 2]
                )
                logger.info(
                    "Surface placement: %d atoms "
                    "in X/Y vicinity (padding=%.1f Å). "
                    "Local Z-max: %.2f Å.",
                    len(vicinity), padding, local_z,
                )
            else:
                local_z = (
                    max(substrate.positions[:, 2])
                    if len(substrate) > 0
                    else 0.0
                )
                logger.info(
                    "Surface placement: no atoms in "
                    "vicinity. Using global Z-max: "
                    "%.2f Å.",
                    local_z,
                )

            placed_min_z = placed.positions[:, 2].min()
            shift = (
                local_z + self.config.distance
            ) - placed_min_z
            logger.info(
                "Z-shift: %.2f Å (local_z %.2f + "
                "distance %.2f − mol_min_z %.2f).",
                shift, local_z,
                self.config.distance, placed_min_z,
            )
            return shift

        # "center" placement
        pz_center = 0.5 * (
            placed.positions[:, 2].max()
            + placed.positions[:, 2].min()
        )
        target_z = 0.5 * substrate.cell.array[2][2]
        return target_z - pz_center

    def _combine_structures(
        self, substrate: Atoms, material: Atoms
    ) -> Atoms:
        """Combine substrate and positioned material.

        Args:
            substrate: The periodic substrate.
            material: The positioned macromolecule.

        Returns:
            A new :class:`~ase.Atoms` object containing both.
        """
        combined = substrate.copy()
        combined.extend(material)
        combined.set_cell(substrate.cell)
        combined.set_pbc([True, True, False])

        # Dynamic Z-vacuum expansion
        max_z = combined.positions[:, 2].max()
        cell_z = combined.cell[2, 2]
        if max_z > cell_z - 5.0:
            logger.info(
                "Molecule exceeds or approaches cell "
                "Z-boundary. Expanding Z-vacuum "
                "dynamically..."
            )
            new_z = max_z + 10.0
            c_vector = combined.cell[2]
            scale_factor = new_z / c_vector[2]
            combined.cell[2] = c_vector * scale_factor

        # Clean up legacy CIF data
        combined.info.pop('occupancy', None)

        return combined

    def build(self) -> Atoms:
        """Execute the build process.

        Build decisions are captured in an internal log that
        is later written to the manifest via
        :meth:`write_manifest`.

        Returns:
            The final hybrid :class:`~ase.Atoms` structure.
        """
        self._build_log = _BuildLog()
        self._build_log.attach()
        try:
            return self._build_inner()
        finally:
            self._build_log.detach()

    def _build_inner(self) -> Atoms:
        """Internal build logic (called within log capture).

        Returns:
            The final hybrid :class:`~ase.Atoms` structure.
        """
        logger.info(
            "Building hybrid structure (placement: %s)...",
            self.config.placement,
        )
        material, substrate = self._read_structures()

        # Unwrap substrate across Z boundary
        cell_z = substrate.cell[2, 2]
        if cell_z > 0:
            has_bottom = np.any(
                substrate.positions[:, 2] < 2.0
            )
            has_top = np.any(
                substrate.positions[:, 2] > cell_z - 2.0
            )
            if has_bottom and has_top:
                logger.info(
                    "Substrate Z-wrapping detected. "
                    "Unwrapping..."
                )
                mask = (
                    substrate.positions[:, 2] > 0.5 * cell_z
                )
                substrate.positions[mask, 2] -= cell_z

        logger.info(
            "Wrapping substrate atoms strictly into "
            "X/Y cell boundaries..."
        )
        substrate.set_pbc([True, True, False])
        substrate.wrap()

        logger.info(
            "Positioning material and checking for "
            "collisions (threshold: %.2f Å)...",
            self.config.collision_threshold,
        )
        placed_material = self._place_material(
            material, substrate
        )

        return self._combine_structures(
            substrate, placed_material
        )

    def _get_output_prefix(self) -> str:
        """Return the output filename prefix.

        Returns:
            The user-provided prefix or ``'hybrid_structure'``.
        """
        if self.config.prefix:
            return self.config.prefix
        return "hybrid_structure"

    def write_outputs(
        self, hybrid: Atoms
    ) -> tuple[Path, Path, Path]:
        """Write the hybrid structure to CIF, GEN, and XYZ.

        Args:
            hybrid: The combined structure.

        Returns:
            A tuple ``(cif_path, gen_path, xyz_path)``.
        """
        prefix = self._get_output_prefix()
        cif_path = self.config.outdir / f"{prefix}.cif"
        gen_path = self.config.outdir / f"{prefix}.gen"
        xyz_path = self.config.outdir / f"{prefix}.xyz"

        logger.info("Writing output files...")
        write(cif_path, hybrid)
        write(gen_path, hybrid, format="gen")
        write(xyz_path, hybrid)

        return cif_path, gen_path, xyz_path

    # ----------------------------------------------------------
    # Build manifest for experiment provenance
    # ----------------------------------------------------------
    def write_manifest(self, hybrid: Atoms) -> Path:
        """Write a JSON manifest next to the output files.

        The manifest captures all inputs, parameters, and
        a git SHA (when available) so that every generated
        structure is fully reproducible.

        Args:
            hybrid: The combined structure (used for stats).

        Returns:
            The path to the written manifest file.
        """
        # pylint: disable=import-outside-toplevel
        from pyhyb.info import __version__

        git_sha = _get_git_sha()

        manifest = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "pyhyb_version": __version__,
            "git_sha": git_sha,
            "material_file": self.config.material_path.name,
            "substrate_file": (
                self.config.substrate_path.name
            ),
            "placement": self.config.placement,
            "distance_angstrom": self.config.distance,
            "collision_threshold_angstrom": (
                self.config.collision_threshold
            ),
            "rotation_degrees": self.config.rotation,
            "optimize": self.config.optimize,
            "total_atoms": len(hybrid),
            "cell_z_angstrom": float(hybrid.cell[2, 2]),
            "build_decisions": (
                list(self._build_log.entries)
            ),
        }

        prefix = self._get_output_prefix()
        manifest_path = (
            self.config.outdir / f"{prefix}_manifest.json"
        )
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)

        logger.info("Build manifest written: %s", manifest_path)
        return manifest_path


def _get_git_sha() -> str | None:
    """Return the current git commit SHA, or *None*.

    Returns:
        The short SHA string, or ``None`` if not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None
