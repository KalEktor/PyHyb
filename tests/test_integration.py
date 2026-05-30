# -*- coding: utf-8 -*-
# pylint: disable=too-many-locals
"""
Integration tests using real example data files.

These tests exercise the full end-to-end pipeline
(file I/O, builder, and output writing) against the
actual glycine, crown ether, and cucurbituril
structures shipped in ``example/data/``.
"""
import json
import pathlib
import tempfile
import unittest

import numpy as np
from ase.io import read
from scipy.spatial.distance import cdist

from pyhyb.core.runner import run_build_hybrid
from pyhyb.tools.builder import (
    HybridBuilder,
    HybridConfig,
)

DATA_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "example" / "data"
)


def _skip_if_missing():
    """Skip if example data is not present."""
    return not (DATA_DIR / "glycine.xyz").exists()


@unittest.skipIf(
    _skip_if_missing(),
    "Example data not found",
)
class TestIntegrationGlycine(unittest.TestCase):
    """End-to-end test: glycine on 7x7 graphene."""

    def test_glycine_surface_build(self):
        """Build glycine/graphene and verify outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            msg = run_build_hybrid(
                material_path=str(
                    DATA_DIR / "glycine.xyz"
                ),
                substrate_path=str(
                    DATA_DIR / "graphene_7x7.cif"
                ),
                output_dir=tmpdir,
                placement="surface",
                distance=3.0,
                collision_threshold=1.5,
            )
            self.assertIn("success", msg.lower())

            out = pathlib.Path(tmpdir)

            # All three output formats exist
            cif = out / "hybrid_structure.cif"
            gen = out / "hybrid_structure.gen"
            xyz = out / "hybrid_structure.xyz"
            manifest = (
                out / "hybrid_structure_manifest.json"
            )
            for path in [cif, gen, xyz, manifest]:
                self.assertTrue(
                    path.exists(),
                    f"Missing output: {path.name}",
                )

            # Read back and check atom count
            hybrid = read(cif)
            glycine = read(DATA_DIR / "glycine.xyz")
            graphene = read(
                DATA_DIR / "graphene_7x7.cif"
            )
            self.assertEqual(
                len(hybrid),
                len(glycine) + len(graphene),
            )

            # No collision: all interatomic distances
            # should be >= threshold
            sub_pos = hybrid.positions[:len(graphene)]
            mol_pos = hybrid.positions[len(graphene):]
            dists = cdist(mol_pos, sub_pos)
            min_dist = float(np.min(dists))
            self.assertGreaterEqual(min_dist, 1.5)

            # Manifest has correct metadata
            with open(
                manifest, "r", encoding="utf-8"
            ) as fh:
                mf = json.load(fh)
            self.assertEqual(
                mf["material_file"], "glycine.xyz"
            )
            self.assertEqual(
                mf["substrate_file"],
                "graphene_7x7.cif",
            )
            self.assertEqual(
                mf["placement"], "surface"
            )
            self.assertEqual(
                mf["total_atoms"], len(hybrid)
            )

    def test_glycine_center_placement(self):
        """Center placement puts glycine mid-cell."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_build_hybrid(
                material_path=str(
                    DATA_DIR / "glycine.xyz"
                ),
                substrate_path=str(
                    DATA_DIR / "graphene_7x7.cif"
                ),
                output_dir=tmpdir,
                placement="center",
            )
            hybrid = read(
                pathlib.Path(tmpdir)
                / "hybrid_structure.cif"
            )
            graphene = read(
                DATA_DIR / "graphene_7x7.cif"
            )

            mol = hybrid[len(graphene):]
            z_center = 0.5 * (
                mol.positions[:, 2].max()
                + mol.positions[:, 2].min()
            )
            cell_mid = 0.5 * hybrid.cell[2, 2]
            self.assertAlmostEqual(
                z_center, cell_mid, delta=1.0,
            )

    def test_glycine_with_rotation(self):
        """Rotation changes atom positions."""
        with tempfile.TemporaryDirectory() as tmp1, \
                tempfile.TemporaryDirectory() as tmp2:
            run_build_hybrid(
                material_path=str(
                    DATA_DIR / "glycine.xyz"
                ),
                substrate_path=str(
                    DATA_DIR / "graphene_7x7.cif"
                ),
                output_dir=tmp1,
                placement="surface",
                distance=3.0,
            )
            run_build_hybrid(
                material_path=str(
                    DATA_DIR / "glycine.xyz"
                ),
                substrate_path=str(
                    DATA_DIR / "graphene_7x7.cif"
                ),
                output_dir=tmp2,
                placement="surface",
                distance=3.0,
                rotation=[0, 0, 90],
            )
            h1 = read(
                pathlib.Path(tmp1)
                / "hybrid_structure.cif"
            )
            h2 = read(
                pathlib.Path(tmp2)
                / "hybrid_structure.cif"
            )
            graphene = read(
                DATA_DIR / "graphene_7x7.cif"
            )
            n_sub = len(graphene)

            # Molecule positions differ
            mol1 = h1.positions[n_sub:]
            mol2 = h2.positions[n_sub:]
            diff = np.linalg.norm(
                mol1 - mol2, axis=1
            )
            self.assertGreater(
                diff.max(), 0.01,
                "Rotation should change positions",
            )


@unittest.skipIf(
    _skip_if_missing(),
    "Example data not found",
)
class TestIntegrationCrownEther(unittest.TestCase):
    """End-to-end test: crown ether on graphene."""

    def test_crown_ether_build(self):
        """Build crown ether hybrid and verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            msg = run_build_hybrid(
                material_path=str(
                    DATA_DIR / "crown_ether.xyz"
                ),
                substrate_path=str(
                    DATA_DIR / "graphene_7x7.cif"
                ),
                output_dir=tmpdir,
                placement="surface",
                distance=3.0,
                collision_threshold=1.5,
            )
            self.assertIn("success", msg.lower())

            hybrid = read(
                pathlib.Path(tmpdir)
                / "hybrid_structure.cif"
            )
            self.assertGreater(len(hybrid), 0)

            # Verify cell Z is reasonable
            self.assertGreater(
                hybrid.cell[2, 2], 5.0
            )


@unittest.skipIf(
    _skip_if_missing(),
    "Example data not found",
)
class TestIntegrationCucurbituril(unittest.TestCase):
    """End-to-end test: cucurbituril on GO."""

    def test_cucurbituril_on_go(self):
        """Build cucurbituril/GO and verify."""
        go_path = DATA_DIR / "graphene_oxide.cif"
        cb_path = DATA_DIR / "cucurbituril.xyz"

        if not go_path.exists() or not cb_path.exists():
            self.skipTest("GO or CB7 data missing")

        with tempfile.TemporaryDirectory() as tmpdir:
            msg = run_build_hybrid(
                material_path=str(cb_path),
                substrate_path=str(go_path),
                output_dir=tmpdir,
                placement="surface",
                distance=3.0,
                collision_threshold=1.5,
            )
            self.assertIn("success", msg.lower())

            hybrid = read(
                pathlib.Path(tmpdir)
                / "hybrid_structure.cif"
            )
            self.assertGreater(len(hybrid), 0)

            # Verify no collision
            go = read(go_path)
            n_sub = len(go)
            mol_pos = hybrid.positions[n_sub:]
            sub_pos = hybrid.positions[:n_sub]

            dists = cdist(mol_pos, sub_pos)
            min_d = float(np.min(dists))
            self.assertGreaterEqual(min_d, 1.5)


@unittest.skipIf(
    _skip_if_missing(),
    "Example data not found",
)
class TestIntegrationBuilderAPI(unittest.TestCase):
    """Test the direct HybridBuilder API."""

    def test_builder_api_writes_manifest(self):
        """Direct API produces all outputs + manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HybridConfig(
                material_path=(
                    DATA_DIR / "glycine.xyz"
                ),
                substrate_path=(
                    DATA_DIR / "graphene_7x7.cif"
                ),
                outdir=pathlib.Path(tmpdir),
                placement="surface",
                distance=3.0,
                collision_threshold=1.5,
            )
            builder = HybridBuilder(config)
            hybrid = builder.build()

            cif, gen, xyz = builder.write_outputs(
                hybrid
            )
            manifest = builder.write_manifest(hybrid)

            self.assertTrue(cif.exists())
            self.assertTrue(gen.exists())
            self.assertTrue(xyz.exists())
            self.assertTrue(manifest.exists())

            with open(
                manifest, "r", encoding="utf-8"
            ) as fh:
                mf = json.load(fh)
            self.assertIn("pyhyb_version", mf)
            self.assertIn("git_sha", mf)


if __name__ == '__main__':
    unittest.main()
