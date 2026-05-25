# -*- coding: utf-8 -*-
# pylint: disable=protected-access,unused-argument,no-member,too-many-locals
"""
Unit Tests for PyHyB HybridBuilder
----------------------------------
Thoroughly tests the 3D material construction algorithms in builder.py.
"""

import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from ase import Atoms
from pyhyb.tools.builder import (
    HybridBuilder,
    HybridConfig,
    InputFileError,
    StructureError
)


class TestBuilder(unittest.TestCase):
    """Test suite for HybridBuilder's geometric manipulation and validation rules."""

    def setUp(self):
        # Default mock config paths
        self.config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("output_dir"),
            placement="center",
            distance=3.0,
            collision_threshold=1.5
        )

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    def test_validation_file_extensions(self, mock_is_file):
        """Verify that incorrect file extensions correctly raise InputFileError."""
        # Non-xyz material
        bad_config1 = HybridConfig(
            material_path=Path("molecule.pdb"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out")
        )
        with self.assertRaises(InputFileError):
            HybridBuilder(bad_config1)

        # Non-cif substrate
        bad_config2 = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.xyz"),
            outdir=Path("out")
        )
        with self.assertRaises(InputFileError):
            HybridBuilder(bad_config2)

    @patch('pyhyb.tools.builder.Path.is_file')
    def test_validation_file_existence(self, mock_is_file):
        """Verify that missing files raise InputFileError."""
        # Material missing
        mock_is_file.side_effect = lambda: False
        with self.assertRaises(InputFileError):
            HybridBuilder(self.config)

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_read_structures_empty_or_no_cell(self, mock_read, mock_is_file):
        """Verify that empty structures or invalid unit cells raise StructureError."""
        builder = HybridBuilder(self.config)

        # 1. Empty material
        mock_read.side_effect = [Atoms(), Atoms("Au", positions=[[0, 0, 0]], cell=[5, 5, 5])]
        with self.assertRaises(StructureError):
            builder._read_structures()

        # 2. Empty substrate
        mock_read.side_effect = [
            Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]]),
            Atoms()
        ]
        with self.assertRaises(StructureError):
            builder._read_structures()

        # 3. Substrate with invalid unit cell rank/volume
        bad_substrate = Atoms("Au", positions=[[0, 0, 0]]) # No cell defined
        mock_read.side_effect = [
            Atoms("H2O", positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]]),
            bad_substrate
        ]
        with self.assertRaises(StructureError):
            builder._read_structures()

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_substrate_unwrapping_and_wrapping(self, mock_read, mock_is_file):
        """Verify substrate Z-unwrapping and horizontal periodic wrapping."""
        # Substrate cell height is 10.0. One atom is at Z=0.1, another wrapped at Z=9.9
        substrate = Atoms(
            "C2",
            positions=[[1.0, 1.0, 0.1], [1.0, 1.0, 9.9]],
            cell=[10.0, 10.0, 10.0]
        )
        # Material is simple
        material = Atoms("H", positions=[[0.0, 0.0, 0.0]])

        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(self.config)
        combined = builder.build()

        # The atom originally at Z=9.9 should be unwrapped to 9.9 - 10.0 = -0.1
        # Since combined has substrate first, check the second atom position
        sub_atoms = combined[:2]
        self.assertAlmostEqual(sub_atoms.positions[1, 2], -0.1)

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_fractional_centering(self, mock_read, mock_is_file):
        """Verify macromolecule fractional bounding box is centered at (0.5, 0.5)."""
        substrate = Atoms("C", positions=[[0, 0, 0]], cell=[10.0, 10.0, 10.0])
        # Molecule is off-center, with bounds X: [1.0, 3.0], Y: [2.0, 4.0]
        # Bounding box center is X=2.0, Y=3.0.
        material = Atoms("H2", positions=[[1.0, 2.0, 0.0], [3.0, 4.0, 0.0]])

        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(self.config)
        combined = builder.build()

        # The molecule atoms start at index 1 of the combined structure
        placed_mol = combined[1:]
        frac_coords = substrate.cell.scaled_positions(placed_mol.positions)

        # Center of fractional bounding box should be exactly at 0.5 in X and Y
        frac_center_x = 0.5 * (frac_coords[:, 0].max() + frac_coords[:, 0].min())
        frac_center_y = 0.5 * (frac_coords[:, 1].max() + frac_coords[:, 1].min())

        self.assertAlmostEqual(frac_center_x, 0.5)
        self.assertAlmostEqual(frac_center_y, 0.5)

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_vertical_placement_modes(self, mock_read, mock_is_file):
        """Verify both center and surface vertical placement algorithms."""
        # Substrate cell height 10.0, substrate atom at Z=2.0
        substrate = Atoms("C", positions=[[5.0, 5.0, 2.0]], cell=[10.0, 10.0, 10.0])
        # Molecule of height 1.0 (Z from 0.0 to 1.0)
        material = Atoms("H2", positions=[[5.0, 5.0, 0.0], [5.0, 5.0, 1.0]])

        # 1. Placement = "center": vertical midpoint centered in cell (Z=5.0)
        config_center = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="center"
        )
        mock_read.side_effect = [material.copy(), substrate.copy()]
        builder_center = HybridBuilder(config_center)
        combined_center = builder_center.build()
        placed_mol_c = combined_center[1:]
        z_center = 0.5 * (
            placed_mol_c.positions[:, 2].max() +
            placed_mol_c.positions[:, 2].min()
        )
        self.assertAlmostEqual(z_center, 5.0)

        # 2. Placement = "surface" with distance = 3.0
        config_surface = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=3.0,
            collision_threshold=1.0 # low to avoid pushing trigger
        )
        mock_read.side_effect = [material.copy(), substrate.copy()]
        builder_surface = HybridBuilder(config_surface)
        combined_surface = builder_surface.build()
        placed_mol_s = combined_surface[1:]
        # Molecule bottom (min Z) should be at substrate_peak + distance = 2.0 + 3.0 = 5.0
        min_z = placed_mol_s.positions[:, 2].min()
        self.assertAlmostEqual(min_z, 5.0)

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_collision_avoidance(self, mock_read, mock_is_file):
        """Verify iterative Z-push collision avoidance works when atoms overlap."""
        # Substrate atom at Z=2.0
        substrate = Atoms("C", positions=[[5.0, 5.0, 2.0]], cell=[10.0, 10.0, 10.0])
        # Molecule placed directly at Z=2.0 in X/Y plane, initially colliding
        material = Atoms("H", positions=[[5.0, 5.0, 0.0]])

        # Set collision threshold = 2.0. With surface distance = 0.0 (starts at Z=2.0)
        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=0.0,
            collision_threshold=2.0
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        placed_mol = combined[1:]
        # Atom must be pushed up until distance is at least 2.0 (Z >= 4.0)
        self.assertGreaterEqual(placed_mol.positions[0, 2], 4.0)

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_dynamic_z_vacuum_expansion(self, mock_read, mock_is_file):
        """Verify dynamic cell Z-expansion when molecule exceeds cell boundaries."""
        # Cell Z is 10.0, substrate atom at Z=0.0
        substrate = Atoms("C", positions=[[0, 0, 0]], cell=[10.0, 10.0, 10.0])
        # Molecule placed high up (near Z=9.5)
        material = Atoms("H", positions=[[5.0, 5.0, 9.5]])

        # Center places at Z=5.0. Use surface with distance=9.5
        config = HybridConfig(
            material_path=Path("molecule.xyz"),
            substrate_path=Path("substrate.cif"),
            outdir=Path("out"),
            placement="surface",
            distance=9.5,
            collision_threshold=0.5
        )
        mock_read.side_effect = [material, substrate]
        builder = HybridBuilder(config)
        combined = builder.build()

        # Highest atom is at Z = 9.5. This exceeds cell_z - 5.0 (which is 5.0).
        # Vacuum expansion should resize the Z lattice vector (cell[2, 2])
        # to max_z + 10.0 = 9.5 + 10.0 = 19.5
        self.assertAlmostEqual(combined.cell[2, 2], 19.5)

    @patch('pyhyb.tools.builder.Path.is_file', return_value=True)
    @patch('pyhyb.tools.builder.read')
    def test_cucurbituril_channel_alignment(self, mock_read, mock_is_file):
        """Verify specialized channel alignment logic for Cucurbituril molecules."""
        # Construct mock 84-atom Cucurbituril structure with exactly 14 Oxygen atoms.
        # Rest can be generic C/H/N atoms.
        symbols = ['O'] * 14 + ['C'] * 70
        positions = np.zeros((84, 3))

        # Position portal oxygens so the channel axis is vertical (along Z-axis)
        # Centroid of top portal (7 oxygens at Z=3.0)
        positions[:7] = [
            [1.0, 0.0, 3.0], [0.5, 0.86, 3.0], [-0.5, 0.86, 3.0],
            [-1.0, 0.0, 3.0], [-0.5, -0.86, 3.0], [0.5, -0.86, 3.0], [0.0, 0.0, 3.0]
        ]
        # Centroid of bottom portal (7 oxygens at Z=-3.0)
        positions[7:14] = [
            [1.0, 0.0, -3.0], [0.5, 0.86, -3.0], [-0.5, 0.86, -3.0],
            [-1.0, 0.0, -3.0], [-0.5, -0.86, -3.0], [0.5, -0.86, -3.0], [0.0, 0.0, -3.0]
        ]
        # Populate other atoms
        positions[14:] = np.random.uniform(-2.0, 2.0, size=(70, 3))

        cucurbituril = Atoms(symbols=symbols, positions=positions)
        substrate = Atoms("C", positions=[[0, 0, 0]], cell=[15.0, 15.0, 15.0])

        mock_read.side_effect = [cucurbituril, substrate]
        builder = HybridBuilder(self.config)
        combined = builder.build()

        # Extract placed Cucurbituril (starting at index 1)
        placed = combined[1:]
        o_indices = [i for i, sym in enumerate(placed.symbols) if sym == 'O']
        o_pos = placed.positions[o_indices]

        # Top and bottom portals
        ring1 = o_pos[:7]
        ring2 = o_pos[7:14]
        c1 = ring1.mean(axis=0)
        c2 = ring2.mean(axis=0)

        # The axis vector should now be perfectly parallel to Cartesian X-axis
        axis = c1 - c2 if c1[2] > c2[2] else c2 - c1
        axis /= np.linalg.norm(axis)

        self.assertAlmostEqual(abs(axis[0]), 1.0, places=4)
        self.assertAlmostEqual(axis[1], 0.0, places=4)
        self.assertAlmostEqual(axis[2], 0.0, places=4)


if __name__ == '__main__':
    unittest.main()
