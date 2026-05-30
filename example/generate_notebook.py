# -*- coding: utf-8 -*-
"""Generate the PyHyB tutorial Jupyter notebook."""
import json
from pathlib import Path


def make_cell(
    cell_type, source, outputs=None, execution_count=None
):
    """Create a notebook cell dict."""
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": source if isinstance(source, list) else [source],
    }
    if cell_type == "code":
        cell["execution_count"] = execution_count
        cell["outputs"] = outputs or []
    return cell


def build_notebook():
    """Build the tutorial notebook structure."""
    cells = []

    # Title
    cells.append(make_cell("markdown", [
        "# 🧬 PyHyB Tutorial: Building Hybrid Molecular Structures\n",
        "\n",
        "This notebook walks through the complete PyHyB workflow:\n",
        "\n",
        "1. **Understanding inputs** — What are `.xyz` and `.cif` files?\n",
        "2. **Building a hybrid** — Deposit a molecule on a substrate\n",
        "3. **Inspecting results** — Examine the combined structure\n",
        "4. **Tuning parameters** — Placement, rotation, collision threshold\n",
        "5. **Reading the manifest** — Provenance and reproducibility\n",
        "\n",
        "---"
    ]))

    # Setup
    cells.append(make_cell("markdown", [
        "## 1. Setup & Imports\n",
        "\n",
        "Make sure PyHyB is installed (`pip install -e .` from the repo root)."
    ]))

    cells.append(make_cell("code", [
        "import sys\n",
        "from pathlib import Path\n",
        "\n",
        "# Ensure PyHyB is importable\n",
        "PROJECT_ROOT = Path('.').resolve()\n",
        "if str(PROJECT_ROOT) not in sys.path:\n",
        "    sys.path.insert(0, str(PROJECT_ROOT))\n",
        "\n",
        "from pyhyb.core.runner import run_build_hybrid\n",
        "from pyhyb.tools.builder import HybridBuilder, HybridConfig\n",
        "from pyhyb.info import __version__, PROGRAM_NAME\n",
        "\n",
        "print(f'{PROGRAM_NAME} v{__version__} loaded successfully!')"
    ]))

    # Understanding inputs
    cells.append(make_cell("markdown", [
        "## 2. Understanding Input Files\n",
        "\n",
        "PyHyB takes two inputs:\n",
        "\n",
        "| Input | Format | Description |\n",
        "|-------|--------|-------------|\n",
        "| **Material** | `.xyz` | The molecule to deposit (e.g., glycine, crown ether) |\n",
        "| **Substrate** | `.cif` | The periodic substrate (e.g., graphene) |\n",
        "\n",
        "Let's examine the example data:"
    ]))

    cells.append(make_cell("code", [
        "from ase.io import read\n",
        "\n",
        "DATA = PROJECT_ROOT / 'example' / 'data'\n",
        "\n",
        "# Read the glycine molecule\n",
        "glycine = read(DATA / 'glycine.xyz')\n",
        "print(f'Glycine: {len(glycine)} atoms')\n",
        "print(f'  Elements: {set(glycine.symbols)}')\n",
        "print(f'  Bounding box (Å):')\n",
        "for axis, name in enumerate(['X', 'Y', 'Z']):\n",
        "    lo = glycine.positions[:, axis].min()\n",
        "    hi = glycine.positions[:, axis].max()\n",
        "    print(f'    {name}: {lo:.2f} — {hi:.2f} (span: {hi-lo:.2f})')\n",
        "\n",
        "# Read the graphene substrate\n",
        "graphene = read(DATA / 'graphene_7x7.cif')\n",
        "print(f'\\nGraphene 7×7: {len(graphene)} atoms')\n",
        "print(f'  Cell dimensions: {graphene.cell.lengths()}')"
    ]))

    # Simple build
    cells.append(make_cell("markdown", [
        "## 3. Building Your First Hybrid Structure\n",
        "\n",
        "The simplest way to build a hybrid is using `run_build_hybrid()`:"
    ]))

    cells.append(make_cell("code", [
        "import tempfile\n",
        "\n",
        "# Use a temporary directory for outputs\n",
        "with tempfile.TemporaryDirectory() as tmpdir:\n",
        "    msg = run_build_hybrid(\n",
        "        material_path=str(DATA / 'glycine.xyz'),\n",
        "        substrate_path=str(DATA / 'graphene_7x7.cif'),\n",
        "        output_dir=tmpdir,\n",
        "        placement='surface',     # Place on top of substrate\n",
        "        distance=3.0,            # 3 Å above the surface\n",
        "        collision_threshold=1.5, # Min 1.5 Å between atoms\n",
        "    )\n",
        "    print(msg)"
    ]))

    # Inspecting results
    cells.append(make_cell("markdown", [
        "## 4. Inspecting the Result\n",
        "\n",
        "Let's build again and examine the combined structure in detail:"
    ]))

    cells.append(make_cell("code", [
        "output_dir = PROJECT_ROOT / 'example' / 'output' / 'tutorial'\n",
        "\n",
        "msg = run_build_hybrid(\n",
        "    material_path=str(DATA / 'glycine.xyz'),\n",
        "    substrate_path=str(DATA / 'graphene_7x7.cif'),\n",
        "    output_dir=str(output_dir),\n",
        "    placement='surface',\n",
        "    distance=3.0,\n",
        "    collision_threshold=1.5,\n",
        ")\n",
        "\n",
        "# Read back the generated structure\n",
        "hybrid = read(output_dir / 'hybrid_structure.cif')\n",
        "\n",
        "print(f'Hybrid structure: {len(hybrid)} atoms')\n",
        "print(f'  Elements: {dict(zip(*zip(*[(s, 1) for s in hybrid.symbols])))}')\n",
        "print(f'  Cell Z-height: {hybrid.cell[2, 2]:.2f} Å')\n",
        "print(f'  Z range: {hybrid.positions[:, 2].min():.2f} — {hybrid.positions[:, 2].max():.2f} Å')"
    ]))

    # Parameters
    cells.append(make_cell("markdown", [
        "## 5. Tuning Parameters\n",
        "\n",
        "### Placement modes\n",
        "\n",
        "| Mode | Description |\n",
        "|------|-------------|\n",
        "| `'surface'` | Bottom of molecule placed `distance` Å above the highest local substrate atom |\n",
        "| `'center'` | Centre of molecule placed at Z = cell_height / 2 (intercalation) |\n",
        "\n",
        "### Rotation\n",
        "\n",
        "You can pre-rotate the molecule around its centre of mass using Euler angles `[rx, ry, rz]` in degrees."
    ]))

    cells.append(make_cell("code", [
        "import tempfile\n",
        "\n",
        "# Compare center vs surface placement\n",
        "for mode in ['center', 'surface']:\n",
        "    with tempfile.TemporaryDirectory() as tmpdir:\n",
        "        run_build_hybrid(\n",
        "            material_path=str(DATA / 'glycine.xyz'),\n",
        "            substrate_path=str(DATA / 'graphene_7x7.cif'),\n",
        "            output_dir=tmpdir,\n",
        "            placement=mode,\n",
        "            distance=3.0,\n",
        "            collision_threshold=1.5,\n",
        "        )\n",
        "        h = read(Path(tmpdir) / 'hybrid_structure.cif')\n",
        "        z_min = h.positions[:, 2].min()\n",
        "        z_max = h.positions[:, 2].max()\n",
        "        print(f'{mode:>8s}: Z range = [{z_min:.1f}, {z_max:.1f}] Å')"
    ]))

    cells.append(make_cell("code", [
        "# Build with a 45° rotation around Z\n",
        "with tempfile.TemporaryDirectory() as tmpdir:\n",
        "    run_build_hybrid(\n",
        "        material_path=str(DATA / 'glycine.xyz'),\n",
        "        substrate_path=str(DATA / 'graphene_7x7.cif'),\n",
        "        output_dir=tmpdir,\n",
        "        placement='surface',\n",
        "        distance=3.0,\n",
        "        collision_threshold=1.5,\n",
        "        rotation=[0, 0, 45],  # 45° around Z-axis\n",
        "    )\n",
        "    h = read(Path(tmpdir) / 'hybrid_structure.cif')\n",
        "    print(f'Rotated hybrid: {len(h)} atoms')\n",
        "    print(f'  Z range: [{h.positions[:, 2].min():.1f}, {h.positions[:, 2].max():.1f}] Å')"
    ]))

    # Manifest
    cells.append(make_cell("markdown", [
        "## 6. Build Manifest (Provenance)\n",
        "\n",
        "Every build writes a `*_manifest.json` alongside the output files.\n",
        "This captures all inputs, parameters, and metadata for reproducibility."
    ]))

    cells.append(make_cell("code", [
        "import json\n",
        "\n",
        "manifest_path = output_dir / 'hybrid_structure_manifest.json'\n",
        "with open(manifest_path) as f:\n",
        "    manifest = json.load(f)\n",
        "\n",
        "for key, value in manifest.items():\n",
        "    print(f'  {key}: {value}')"
    ]))

    # Advanced: programmatic API
    cells.append(make_cell("markdown", [
        "## 7. Advanced: Using the Builder API Directly\n",
        "\n",
        "For more control, use `HybridConfig` + `HybridBuilder` directly:"
    ]))

    cells.append(make_cell("code", [
        "config = HybridConfig(\n",
        "    material_path=DATA / 'crown_ether.xyz',\n",
        "    substrate_path=DATA / 'graphene_7x7.cif',\n",
        "    outdir=output_dir / 'crown_ether_advanced',\n",
        "    placement='surface',\n",
        "    distance=2.5,\n",
        "    collision_threshold=1.8,\n",
        "    rotation=[0, 0, 30],\n",
        ")\n",
        "\n",
        "builder = HybridBuilder(config)\n",
        "hybrid = builder.build()\n",
        "\n",
        "# Write outputs\n",
        "cif, gen, xyz = builder.write_outputs(hybrid)\n",
        "manifest = builder.write_manifest(hybrid)\n",
        "\n",
        "print(f'Crown ether hybrid: {len(hybrid)} atoms')\n",
        "print(f'  CIF: {cif}')\n",
        "print(f'  Manifest: {manifest}')"
    ]))

    # Default parameters
    cells.append(make_cell("markdown", [
        "## 8. Default Parameters\n",
        "\n",
        "All parameter defaults are centralised in `HybridConfig.defaults()`:"
    ]))

    cells.append(make_cell("code", [
        "from pyhyb.tools.builder import HybridConfig\n",
        "\n",
        "defaults = HybridConfig.defaults()\n",
        "for key, value in defaults.items():\n",
        "    print(f'  {key}: {value}')"
    ]))

    # Summary
    cells.append(make_cell("markdown", [
        "## 📝 Summary\n",
        "\n",
        "| Feature | How to use |\n",
        "|---------|------------|\n",
        "| Quick build | `run_build_hybrid(material, substrate, ...)` |\n",
        "| Advanced build | `HybridConfig` + `HybridBuilder` |\n",
        "| Placement modes | `'center'` (intercalation) or `'surface'` (deposition) |\n",
        "| Rotation | `rotation=[rx, ry, rz]` in degrees |\n",
        "| Collision safety | `collision_threshold` in Å |\n",
        "| Provenance | `*_manifest.json` auto-generated |\n",
        "| Web GUI | `streamlit run app.py` |\n",
        "| Interactive menu | `python launcher.py` |\n",
        "\n",
        "---\n",
        "\n",
        "For more details, see the [README.md](../README.md) or the Streamlit Web GUI."
    ]))

    # Assemble notebook
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.12.0"
            }
        },
        "cells": cells,
    }

    return notebook


if __name__ == '__main__':
    nb = build_notebook()
    out_path = Path(__file__).parent / 'tutorial.ipynb'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f'Notebook written to {out_path}')
