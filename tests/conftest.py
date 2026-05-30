# -*- coding: utf-8 -*-
# pylint: disable=import-error,duplicate-code
"""
Shared pytest fixtures for PyHyB test suite.

Provides reusable substrate, material, and config objects
so that test files don't duplicate mock setup boilerplate.
These fixtures are auto-discovered by pytest.
"""
from pathlib import Path
from unittest.mock import patch

import pytest
from ase import Atoms

from pyhyb.tools.builder import HybridConfig, HybridBuilder
from tests.helpers import build_mock_cucurbituril


# ----------------------------------------------------------
# Structural fixtures
# ----------------------------------------------------------

@pytest.fixture
def simple_substrate():
    """A minimal 10 Å cubic substrate with one C atom."""
    return Atoms(
        "C",
        positions=[[0.0, 0.0, 0.0]],
        cell=[10.0, 10.0, 10.0],
    )


@pytest.fixture
def simple_material():
    """A two-atom H2 molecule."""
    return Atoms(
        "H2",
        positions=[
            [5.0, 5.0, 0.0],
            [5.0, 5.0, 1.0],
        ],
    )


@pytest.fixture
def large_substrate():
    """A 100 Å cubic substrate for vicinity tests."""
    return Atoms(
        "C2",
        positions=[
            [50.0, 50.0, 2.0],
            [90.0, 90.0, 8.0],
        ],
        cell=[100.0, 100.0, 100.0],
    )


@pytest.fixture
def linear_molecule():
    """A linear molecule spanning 12 Å along X."""
    return Atoms(
        "H2",
        positions=[
            [-6.0, 0.0, 0.0],
            [6.0, 0.0, 0.0],
        ],
    )


@pytest.fixture
def square_molecule():
    """A 12x12 Å square molecule in the X-Y plane."""
    return Atoms(
        "H4",
        positions=[
            [-6.0, -6.0, 0.0],
            [6.0, -6.0, 0.0],
            [6.0, 6.0, 0.0],
            [-6.0, 6.0, 0.0],
        ],
    )


@pytest.fixture
def mock_cucurbituril():
    """A synthetic 84-atom cucurbituril structure."""
    return build_mock_cucurbituril()


# ----------------------------------------------------------
# Config fixtures
# ----------------------------------------------------------

@pytest.fixture
def default_config(tmp_path):
    """A HybridConfig with default parameters."""
    return HybridConfig(
        material_path=Path("molecule.xyz"),
        substrate_path=Path("substrate.cif"),
        outdir=tmp_path,
        placement="center",
        distance=3.0,
        collision_threshold=1.5,
    )


@pytest.fixture
def surface_config(tmp_path):
    """A HybridConfig with surface placement."""
    return HybridConfig(
        material_path=Path("molecule.xyz"),
        substrate_path=Path("substrate.cif"),
        outdir=tmp_path,
        placement="surface",
        distance=3.0,
        collision_threshold=1.5,
    )


# ----------------------------------------------------------
# Builder helper
# ----------------------------------------------------------

@pytest.fixture
def make_builder():
    """Factory fixture to create a HybridBuilder.

    Patches ``Path.is_file`` and ``ase.io.read`` so that
    tests can supply synthetic structures without files.
    """
    def _make(config, material, substrate):
        with patch(
            'pyhyb.tools.builder.Path.is_file',
            return_value=True,
        ), patch(
            'pyhyb.tools.builder.read',
            side_effect=[material, substrate],
        ):
            builder = HybridBuilder(config)
            combined = builder.build()
        return builder, combined

    return _make
