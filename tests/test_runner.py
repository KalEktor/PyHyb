# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
# pylint: disable=unused-argument,unused-variable
"""
Unit Tests for PyHyB Workflow Runner & Structure Optimizer.
"""

import unittest
from unittest.mock import patch, MagicMock

from ase import Atoms

from pyhyb.core.hybrid_runner import HybridWorkflowRunner
from pyhyb.tools.optimizer import StructureOptimizer


class TestRunnerAndOptimizer(unittest.TestCase):
    """Tests for the workflow orchestrator and optimiser."""

    @patch('pyhyb.tools.optimizer.os.environ.get')
    def test_optimizer_requires_dftb_prefix(self, mock):
        """Fails gracefully if DFTB_PREFIX is missing."""
        mock.return_value = None
        opt = StructureOptimizer()
        atoms = Atoms("Au", positions=[[0, 0, 0]])

        with self.assertRaises(RuntimeError) as ctx:
            opt.optimize(atoms)
        self.assertIn(
            "DFTB_PREFIX environment variable is not set",
            str(ctx.exception),
        )

    @patch('pyhyb.tools.optimizer.os.environ.get')
    @patch('pyhyb.tools.optimizer.Path.exists')
    def test_optimizer_requires_existing_prefix(
        self, mock_exists, mock_env
    ):
        """Fails if DFTB_PREFIX path doesn't exist."""
        mock_env.return_value = "/path/to/missing/sk"
        mock_exists.return_value = False
        opt = StructureOptimizer()
        atoms = Atoms("Au", positions=[[0, 0, 0]])

        with self.assertRaises(RuntimeError) as ctx:
            opt.optimize(atoms)
        self.assertIn(
            "specified by DFTB_PREFIX does not exist",
            str(ctx.exception),
        )

    @patch(
        'pyhyb.tools.optimizer.os.environ.get',
        return_value="/mock/prefix",
    )
    @patch(
        'pyhyb.tools.optimizer.Path.exists',
        return_value=True,
    )
    @patch('pyhyb.tools.optimizer.BFGS')
    @patch('pyhyb.tools.optimizer.Dftb')
    @patch(
        'pyhyb.tools.optimizer.Atoms'
        '.get_potential_energy',
    )
    def test_optimizer_relaxation_pipeline(
        self, mock_energy, mock_dftb, mock_bfgs,
        mock_exists, mock_env,
    ):
        """Optimizer attaches Dftb and runs BFGS."""
        mock_energy.side_effect = [-100.0, -105.0]
        mock_bfgs_inst = MagicMock()
        mock_bfgs.return_value = mock_bfgs_inst

        opt = StructureOptimizer(
            fmax=0.05, steps=10,
            workdir="/tmp/mock_workdir",
        )
        atoms = Atoms(
            "H2",
            positions=[[0, 0, 0], [0, 0, 1]],
            cell=[5, 5, 5],
        )

        opt_atoms, init_e, final_e = opt.optimize(atoms)

        mock_dftb.assert_called_once_with(
            directory="/tmp/mock_workdir",
            kpts=(1, 1, 1),
        )
        self.assertEqual(init_e, -100.0)
        self.assertEqual(final_e, -105.0)
        mock_bfgs_inst.run.assert_called_once_with(
            fmax=0.05, steps=10,
        )

    @patch(
        'pyhyb.core.hybrid_runner.Path.exists',
        return_value=True,
    )
    def test_workflow_runner_input_validation(self, _):
        """HybridWorkflowRunner checks suffix errors."""
        runner = HybridWorkflowRunner()

        success, msg = runner.run(
            material_path="molecule.pdb",
            substrate_path="substrate.cif",
        )
        self.assertFalse(success)
        self.assertIn("Material must be .xyz", msg)

        success, msg = runner.run(
            material_path="molecule.xyz",
            substrate_path="substrate.xyz",
        )
        self.assertFalse(success)
        self.assertIn("Substrate must be .cif", msg)


if __name__ == '__main__':
    unittest.main()
