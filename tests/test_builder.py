# -*- coding: utf-8 -*-
# pylint: disable=protected-access,unused-argument
# pylint: disable=no-member,too-many-locals
"""
Unit Tests for PyHyB HybridBuilder.

Thoroughly tests the 3D material construction algorithms in
builder.py, including deterministic numerical tests for
collision avoidance, auto-tilt, Euler rotation, and cell
expansion.
"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from ase import Atoms

from pyhyb.tools.builder import (
    HybridBuilder,
    HybridConfig,
    InputFileError,
    StructureError,
)


class TestBuilder(unittest.TestCase):
    """Test suite for HybridBuilder's geometric logic."""

    def setUp(self):
        """Set up default mock config paths."""
        self.config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("output_dir"),
            placement="center",
            distance=3.0,
            collision_threshold=1.5,
        )

    # --------------------------------------------------
    # Validation tests
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    def test_validation_file_extensions(self, _):
        """Bad extensions raise InputFileError."""
        bad1 = HybridConfig(
            material_path=Path("molecule.pdb"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
        )
        with self.assertRaises(InputFileError):
            HybridBuilder(bad1)

        bad2 = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.xyz"),
            outdir=Path("out"),
        )
        with self.assertRaises(InputFileError):
            HybridBuilder(bad2)

    @patch('pyhyb.tools.builder.Path.is_file')
    def test_validation_file_existence(self, mock):
        """Missing files raise InputFileError."""
        mock.side_effect = lambda: False
        with self.assertRaises(InputFileError):
            HybridBuilder(self.config)

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_read_empty_or_no_cell(self, mock_read, _):
        """Empty structures or bad cells raise."""
        builder = HybridBuilder(self.config)

        # Empty material
        mock_read.side_effect = [
            Atoms(),
            Atoms("Au", positions=[[0, 0, 0]],
                  cell=[5, 5, 5]),
        ]
        with self.assertRaises(StructureError):
            builder._read_structures()

        # Empty substrate
        mock_read.side_effect = [
            Atoms("H2O", positions=[
                [0, 0, 0], [0, 0, 1], [0, 1, 0]]),
            Atoms(),
        ]
        with self.assertRaises(StructureError):
            builder._read_structures()

        # Substrate with no cell
        mock_read.side_effect = [
            Atoms("H2O", positions=[
                [0, 0, 0], [0, 0, 1], [0, 1, 0]]),
            Atoms("Au", positions=[[0, 0, 0]]),
        ]
        with self.assertRaises(StructureError):
            builder._read_structures()

    # --------------------------------------------------
    # Substrate pre-processing tests
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_substrate_unwrapping(self, mock_read, _):
        """Verify substrate Z-unwrapping."""
        substrate = Atoms(
            "C2",
            positions=[[1.0, 1.0, 0.1],
                       [1.0, 1.0, 9.9]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H", positions=[[0.0, 0.0, 0.0]]
        )

        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(self.config)
        combined = builder.build()

        sub_atoms = combined[:2]
        self.assertAlmostEqual(
            sub_atoms.positions[1, 2], -0.1
        )

    # --------------------------------------------------
    # Placement tests
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_fractional_centering(self, mock_read, _):
        """Molecule bounding box centred at (0.5, 0.5)."""
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H2",
            positions=[[1.0, 2.0, 0.0],
                       [3.0, 4.0, 0.0]],
        )

        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(self.config)
        combined = builder.build()

        placed = combined[1:]
        frac = substrate.cell.scaled_positions(
            placed.positions
        )

        cx = 0.5 * (
            frac[:, 0].max() + frac[:, 0].min()
        )
        cy = 0.5 * (
            frac[:, 1].max() + frac[:, 1].min()
        )

        self.assertAlmostEqual(cx, 0.5)
        self.assertAlmostEqual(cy, 0.5)

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_vertical_placement_modes(
        self, mock_read, _
    ):
        """Both center and surface Z-positioning work."""
        substrate = Atoms(
            "C", positions=[[5.0, 5.0, 2.0]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H2",
            positions=[[5.0, 5.0, 0.0],
                       [5.0, 5.0, 1.0]],
        )

        # Center placement
        cfg_c = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="center",
        )
        mock_read.side_effect = [
            material.copy(), substrate.copy()
        ]
        builder_c = HybridBuilder(cfg_c)
        combined_c = builder_c.build()
        mol_c = combined_c[1:]
        z_center = 0.5 * (
            mol_c.positions[:, 2].max()
            + mol_c.positions[:, 2].min()
        )
        self.assertAlmostEqual(z_center, 5.0)

        # Surface placement
        cfg_s = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=3.0,
            collision_threshold=1.0,
        )
        mock_read.side_effect = [
            material.copy(), substrate.copy()
        ]
        builder_s = HybridBuilder(cfg_s)
        combined_s = builder_s.build()
        mol_s = combined_s[1:]
        min_z = mol_s.positions[:, 2].min()
        self.assertAlmostEqual(min_z, 5.0)

    # --------------------------------------------------
    # Collision avoidance tests
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_collision_avoidance(self, mock_read, _):
        """Z-push lifts atom above threshold distance."""
        substrate = Atoms(
            "C", positions=[[5.0, 5.0, 2.0]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H", positions=[[5.0, 5.0, 0.0]]
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=0.0,
            collision_threshold=2.0,
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        mol = combined[1:]
        self.assertGreaterEqual(
            mol.positions[0, 2], 4.0
        )

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_collision_zpush_increments(
        self, mock_read, _
    ):
        """Z-push uses 0.1 Å increments until clear.

        Place a single atom exactly at the substrate
        atom position. With threshold=1.0 Å, the push
        must result in a minimum distance >= 1.0 and
        the final Z must be the substrate Z + n*0.1
        where n is the smallest integer satisfying the
        constraint.
        """
        substrate = Atoms(
            "C", positions=[[5.0, 5.0, 0.0]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H", positions=[[5.0, 5.0, 0.0]]
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=0.0,
            collision_threshold=1.0,
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        mol = combined[1:]
        sub = combined[:1]
        dist = np.linalg.norm(
            mol.positions[0] - sub.positions[0]
        )
        self.assertGreaterEqual(dist, 1.0)

        # Verify the Z was moved in 0.1 increments
        dz = mol.positions[0, 2] - sub.positions[0, 2]
        n_steps = round(dz / 0.1)
        self.assertAlmostEqual(
            dz, n_steps * 0.1, places=5
        )

    # --------------------------------------------------
    # Auto-tilt tests
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_auto_tilt_yaw_reduces_span(
        self, mock_read, _
    ):
        """In-plane yaw rotation reduces span < 0.99.

        Create a linear molecule along the X-axis that
        exceeds the cell in X but not diagonally.
        Yaw should rotate it to fit.
        """
        cell_size = 10.0
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[cell_size, cell_size, cell_size],
        )
        # Molecule spans 12 Å along X (> cell 10 Å)
        # but only 0 Å in Y. Diagonal = 12/√2 ≈ 8.5 < 10
        material = Atoms(
            "H2",
            positions=[[-6.0, 0.0, 0.0],
                       [6.0, 0.0, 0.0]],
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="center",
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        # Check the placed molecule fits in cell
        mol = combined[1:]
        frac = substrate.cell.scaled_positions(
            mol.positions
        )
        span = max(
            frac[:, 0].max() - frac[:, 0].min(),
            frac[:, 1].max() - frac[:, 1].min(),
        )
        self.assertLess(span, 0.99)

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_auto_tilt_outofplane_fallback(
        self, mock_read, _
    ):
        """Out-of-plane tilt engages when yaw fails.

        Create a square molecule that exceeds the cell
        in both X and Y — yaw alone cannot fix it but
        tilting out of plane reduces the projection.
        """
        cell_size = 10.0
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[cell_size, cell_size, cell_size],
        )
        # Square 12×12 in X-Y plane: no yaw rotation
        # can reduce this below the cell.
        # But tilting out of the plane projects it
        # smaller.
        positions = [
            [-6.0, -6.0, 0.0],
            [6.0, -6.0, 0.0],
            [6.0, 6.0, 0.0],
            [-6.0, 6.0, 0.0],
        ]
        material = Atoms(
            "H4", positions=positions
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="center",
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        # Even if it couldn't fully fit, the span
        # should be reduced from the original 1.2
        mol = combined[1:]
        frac = substrate.cell.scaled_positions(
            mol.positions
        )
        span = max(
            frac[:, 0].max() - frac[:, 0].min(),
            frac[:, 1].max() - frac[:, 1].min(),
        )
        # Original was 12/10 = 1.2; tilt should reduce
        self.assertLess(span, 1.2)

    # --------------------------------------------------
    # Euler rotation test
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_euler_rotation_applied(
        self, mock_read, _
    ):
        """User rotation changes atom positions.

        A 90° rotation around Z should swap X and Y
        coordinates (with sign changes).
        """
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[20.0, 20.0, 20.0],
        )
        material = Atoms(
            "H2",
            positions=[[1.0, 0.0, 0.0],
                       [-1.0, 0.0, 0.0]],
        )

        # Without rotation — molecule along X
        cfg_no_rot = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="center",
            rotation=None,
        )
        mock_read.side_effect = [
            material.copy(), substrate.copy()
        ]
        builder_nr = HybridBuilder(cfg_no_rot)
        combined_nr = builder_nr.build()
        mol_nr = combined_nr[1:]

        # With 90° Z rotation — molecule along Y
        cfg_rot = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="center",
            rotation=[0.0, 0.0, 90.0],
        )
        mock_read.side_effect = [
            material.copy(), substrate.copy()
        ]
        builder_r = HybridBuilder(cfg_rot)
        combined_r = builder_r.build()
        mol_r = combined_r[1:]

        # After 90° Z rotation, the X-span should
        # become the Y-span
        dx_nr = (
            mol_nr.positions[:, 0].max()
            - mol_nr.positions[:, 0].min()
        )
        dy_r = (
            mol_r.positions[:, 1].max()
            - mol_r.positions[:, 1].min()
        )
        self.assertAlmostEqual(dx_nr, dy_r, places=3)

    # --------------------------------------------------
    # Cell expansion tests
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_dynamic_z_vacuum_expansion(
        self, mock_read, _
    ):
        """Cell Z expands when molecule is near top."""
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H", positions=[[5.0, 5.0, 9.5]]
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=9.5,
            collision_threshold=0.5,
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        self.assertAlmostEqual(
            combined.cell[2, 2], 19.5
        )

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_cell_expansion_preserves_atoms(
        self, mock_read, _
    ):
        """Z-expansion keeps all atoms in place.

        The expansion should only modify cell[2,2],
        not move any atom positions.
        """
        substrate = Atoms(
            "C2",
            positions=[[0, 0, 0], [5, 5, 3]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H", positions=[[5.0, 5.0, 0.0]]
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=9.0,
            collision_threshold=0.5,
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        # Total atoms = 2 substrate + 1 material = 3
        self.assertEqual(len(combined), 3)
        # Cell Z is expanded
        self.assertGreater(
            combined.cell[2, 2], 10.0
        )
        # Original substrate atoms unchanged in X/Y
        self.assertAlmostEqual(
            combined.positions[0, 0], 0.0
        )

    # --------------------------------------------------
    # Surface placement edge case
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_surface_placement_local_vicinity(
        self, mock_read, _
    ):
        """Surface mode uses local substrate max Z.

        When substrate has atoms at different heights,
        placement should use the Z-max of atoms in the
        X/Y vicinity of the molecule, not the global
        maximum.
        """
        # Nearby atom at Z=2, far atom at Z=8
        # Use a 100 Å cell so the far atom (90,90)
        # is well outside the X/Y vicinity padding.
        substrate = Atoms(
            "C2",
            positions=[
                [50.0, 50.0, 2.0],  # nearby
                [90.0, 90.0, 8.0],  # far corner
            ],
            cell=[100.0, 100.0, 100.0],
        )
        # Small molecule near cell centre
        material = Atoms(
            "H", positions=[[50.0, 50.0, 0.0]]
        )

        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=3.0,
            collision_threshold=0.5,
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        mol = combined[2:]
        # Molecule should be at 2.0 + 3.0 = 5.0,
        # not 8.0 + 3.0 = 11.0
        self.assertAlmostEqual(
            mol.positions[0, 2], 5.0, places=0
        )
        self.assertLess(mol.positions[0, 2], 9.0)

    # --------------------------------------------------
    # Cucurbituril alignment test
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_cucurbituril_channel_alignment(
        self, mock_read, _
    ):
        """Channel axis is aligned to X-axis."""
        # Import the shared helper to avoid
        # duplicate-code with conftest
        from tests.helpers import (  # pylint: disable=import-outside-toplevel
            build_mock_cucurbituril,
        )

        cucurbituril = build_mock_cucurbituril()
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[15.0, 15.0, 15.0],
        )

        mock_read.side_effect = [
            cucurbituril, substrate
        ]
        builder = HybridBuilder(self.config)
        combined = builder.build()

        placed = combined[1:]
        o_idx = [
            i for i, sym in enumerate(placed.symbols)
            if sym == 'O'
        ]
        o_pos = placed.positions[o_idx]

        ring1 = o_pos[:7]
        ring2 = o_pos[7:14]
        c1 = ring1.mean(axis=0)
        c2 = ring2.mean(axis=0)

        axis = (
            c1 - c2 if c1[2] > c2[2] else c2 - c1
        )
        axis /= np.linalg.norm(axis)

        self.assertAlmostEqual(
            abs(axis[0]), 1.0, places=4
        )
        self.assertAlmostEqual(
            axis[1], 0.0, places=4
        )
        self.assertAlmostEqual(
            axis[2], 0.0, places=4
        )

    # --------------------------------------------------
    # Build manifest test
    # --------------------------------------------------

    @patch(
        'pyhyb.tools.builder.Path.is_file',
        return_value=True,
    )
    @patch('pyhyb.tools.builder.read')
    def test_write_manifest_content(
        self, mock_read, _
    ):
        """Manifest JSON has all required keys."""
        substrate = Atoms(
            "C", positions=[[0, 0, 0]],
            cell=[10.0, 10.0, 10.0],
        )
        material = Atoms(
            "H", positions=[[5.0, 5.0, 0.0]]
        )

        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(self.config)
        hybrid = builder.build()

        manifest_path = builder.write_manifest(hybrid)
        self.assertTrue(manifest_path.exists())

        with open(
            manifest_path, "r", encoding="utf-8"
        ) as fh:
            manifest = json.load(fh)

        required_keys = [
            "timestamp",
            "pyhyb_version",
            "git_sha",
            "material_file",
            "substrate_file",
            "placement",
            "distance_angstrom",
            "collision_threshold_angstrom",
            "rotation_degrees",
            "optimize",
            "total_atoms",
            "cell_z_angstrom",
            "build_decisions",
        ]
        for key in required_keys:
            self.assertIn(key, manifest)

        self.assertEqual(
            manifest["material_file"], "molecule.xyz"
        )
        self.assertEqual(
            manifest["substrate_file"], "substrate.cif"
        )
        self.assertEqual(
            manifest["placement"], "center"
        )
        self.assertEqual(
            manifest["distance_angstrom"], 3.0
        )
        self.assertEqual(
            manifest["total_atoms"], len(hybrid)
        )

        # Build decisions should be a non-empty list
        decisions = manifest["build_decisions"]
        self.assertIsInstance(decisions, list)
        self.assertGreater(
            len(decisions), 0,
            "Manifest should capture build decisions",
        )

    # --------------------------------------------------
    # HybridConfig.defaults() test
    # --------------------------------------------------

    def test_config_defaults(self):
        """HybridConfig.defaults() returns expected keys."""
        defaults = HybridConfig.defaults()
        self.assertIn("placement", defaults)
        self.assertIn("distance", defaults)
        self.assertIn("collision_threshold", defaults)
        self.assertIn("rotation", defaults)
        self.assertIn("optimize", defaults)
        self.assertEqual(defaults["placement"], "center")
        self.assertEqual(defaults["distance"], 3.0)


if __name__ == '__main__':
    unittest.main()
