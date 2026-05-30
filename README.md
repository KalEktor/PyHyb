# PyHyB — Hybrid Material Builder

[![CI](https://github.com/KalEktor/PyHyb/actions/workflows/ci.yml/badge.svg)](https://github.com/KalEktor/PyHyb/actions/workflows/ci.yml)
[![Pylint Score](https://img.shields.io/badge/pylint-10.00/10-brightgreen)](https://github.com/KalEktor/PyHyb)
[![pycodestyle](https://img.shields.io/badge/pycodestyle-passing-brightgreen)](https://github.com/KalEktor/PyHyb)
[![License](https://img.shields.io/badge/license-LGPLv2.1%2B-blue)](LICENSE)

**PyHyB** is a high-performance Python package for constructing hybrid molecular/substrate configurations using the [Atomic Simulation Environment (ASE)](https://wiki.fysik.dtu.dk/ase/). It automates the difficult process of placing molecular structures on periodic substrates with collision avoidance, auto-tilt fitting, and optional geometry optimisation via DFTB+.

---

## ✨ Key Features

- **3D Material Construction** — Deposit any `.xyz` molecule on any periodic `.cif` substrate
- **Collision Avoidance** — Iterative Z-push algorithm to prevent atomic overlaps
- **Auto-Tilt Fitting** — Automatic yaw/pitch/roll to fit oversized molecules into unit cells
- **Cucurbituril Channel Alignment** — Specialised alignment for macrocyclic host molecules
- **Build Manifest** — Full JSON provenance for every generated structure (inputs, parameters, git SHA, timestamp)
- **Interactive Web GUI** — Beautiful Streamlit dashboard with 3D py3Dmol viewer
- **CLI & Menu Launcher** — Multiple entry points for different workflows
- **Geometry Optimisation** — Optional DFTB+ relaxation via ASE's BFGS optimiser

---

## 📐 Architecture

```
PyHyB/
├── pyhyb/                     # Main package
│   ├── core/                  # Workflow orchestration
│   │   ├── runner.py          # Geni orchestrator & run_build_hybrid()
│   │   ├── hybrid_runner.py   # HybridWorkflowRunner (validation + execution)
│   │   └── main.py            # pyhyb_main() entry point
│   ├── tools/                 # Builder & analysis tools
│   │   ├── builder.py         # HybridBuilder, HybridConfig, build manifest
│   │   ├── optimizer.py       # DFTB+ geometry optimisation
│   │   ├── tools.py           # Segment analysis (local_mean, consistency)
│   │   └── cross_tools.py     # Cross-segment (Pearson, overlap)
│   ├── inout/                 # File I/O helpers
│   │   └── inout.py           # Read .s/.f files, JSON settings
│   ├── bin/                   # CLI entry points
│   │   └── pyhybrun.py        # Console script
│   └── info.py                # Version, logo, metadata
├── tests/                     # Unit + integration tests (40 tests)
├── example/                   # Benchmark examples with data
├── app.py                     # Streamlit Web GUI
├── launcher.py                # Interactive menu launcher
└── run.sh                     # One-click bootstrapper (macOS/Linux)
```

---

## 🚀 Installation

### Manual Install (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/KalEktor/PyHyb.git
cd PyHyb

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode
pip install -e .
```

### One-Click Bootstrap (macOS / Linux)

For users who prefer a single command that handles Python detection, virtual environment creation, and dependency installation:

```bash
chmod +x run.sh
./run.sh
```

This will automatically detect/install Python, create a `.venv`, install dependencies, and launch the interactive menu.

---

## 🔬 Usage

### Python API (programmatic)

```python
from pyhyb.core.runner import run_build_hybrid

# Build a glycine-on-graphene hybrid structure
msg = run_build_hybrid(
    material_path="example/data/glycine.xyz",
    substrate_path="example/data/graphene_7x7.cif",
    output_dir="output/glycine_on_graphene",
    placement="surface",         # or "center"
    distance=3.0,                # Å above substrate
    collision_threshold=1.5,     # minimum allowed distance (Å)
    rotation=[0, 0, 45],         # optional Euler angles (degrees)
)
print(msg)
```

### Interactive Menu

```bash
python launcher.py
```

Choose from: Web GUI launch, interactive builder, benchmark examples, or test suite.

### CLI (non-interactive)

```bash
python launcher.py -m example/data/glycine.xyz \
                   -s example/data/graphene_7x7.cif \
                   -o output/ \
                   -p surface \
                   -d 3.0
```

### Streamlit Web GUI

```bash
streamlit run app.py
```

Opens a browser-based 3D dashboard for uploading structures, adjusting parameters, and visualising results interactively.

### Jupyter Notebook Tutorial

A step-by-step tutorial notebook is provided at `example/tutorial.ipynb`:

```bash
jupyter notebook example/tutorial.ipynb
```

The tutorial covers input inspection, building hybrids, tuning parameters, reading manifests, and using the advanced API.

---

## 📋 Build Manifest

Every build produces a `*_manifest.json` alongside the output files for full experiment provenance:

```json
{
  "timestamp": "2026-05-28T19:00:00+00:00",
  "pyhyb_version": "0.0.9.dev0",
  "git_sha": "abc1234",
  "material_file": "glycine.xyz",
  "substrate_file": "graphene_7x7.cif",
  "placement": "surface",
  "distance_angstrom": 3.0,
  "collision_threshold_angstrom": 1.5,
  "rotation_degrees": null,
  "optimize": false,
  "total_atoms": 108,
  "cell_z_angstrom": 23.45
}
```

---

## 🧪 Examples

Three benchmark examples are included in `example/data/`:

| # | Material | Substrate | Description |
|---|----------|-----------|-------------|
| 1 | `glycine.xyz` | `graphene_7x7.cif` | Amino acid on pristine graphene |
| 2 | `crown_ether.xyz` | `graphene_7x7.cif` | 15-crown-5 macrocycle on graphene |
| 3 | `cucurbituril.xyz` | `graphene_oxide.cif` | CB[7] on graphene oxide |

Run all examples:

```bash
python example/run_examples.py
```

---

## ✅ Testing

```bash
# Run the full test suite (34 tests)
python -m unittest discover -s tests -v

# Or with pytest + coverage (if pytest is installed)
python -m pytest tests/ -v --cov=pyhyb --cov-report=term-missing
```

The test suite includes deterministic numerical tests for:
- Collision avoidance Z-push increments
- Auto-tilt (in-plane yaw and out-of-plane fallback)
- Euler rotation application
- Dynamic Z-vacuum cell expansion
- Surface placement local vicinity
- Cucurbituril channel alignment
- Build manifest generation and validation

---

## 🛠️ Code Quality

| Tool | Status |
|------|--------|
| **pylint** | 10.00/10 |
| **pycodestyle** | 0 violations |
| **Unit Tests** | 34/34 passing |

CI runs all three checks on Python 3.10, 3.11, and 3.12 via GitHub Actions.

---

## ⚗️ Geometry Optimisation (DFTB+)

To enable DFTB+ geometry optimisation, download the Slater-Koster parameter files from [dftb.org](https://dftb.org/parameters/download) matching your elements, and set:

```bash
export DFTB_PREFIX=/path/to/slater-koster-files/
```

Then use `--optimize` on the CLI or tick the option in the GUI.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository and create a feature branch
2. **Write tests** for new functionality (see `tests/` for patterns)
3. **Ensure all checks pass** before submitting:
   ```bash
   pylint pyhyb app.py launcher.py setup.py tests/
   pycodestyle pyhyb/ tests/ app.py launcher.py setup.py
   python -m unittest discover -s tests -v
   ```
4. Submit a **pull request** with a clear description of changes

---

## 📜 License

Distributed under the LGPLv2.1+ License. See `LICENSE` for details.

---

## 📚 Dependencies

- [ASE](https://wiki.fysik.dtu.dk/ase/) ≥ 3.22.0 — Atomic Simulation Environment
- [NumPy](https://numpy.org/) ≥ 1.17.0 — Numerical computing
- [SciPy](https://scipy.org/) ≥ 1.7.0 — Scientific computing
- [Streamlit](https://streamlit.io/) ≥ 1.20.0 — Web GUI framework

---

## 📖 API Documentation

Full API reference is auto-generated from docstrings using Sphinx:

```bash
pip install -e .[docs]
cd docs && make html
```

The generated HTML will be in `docs/_build/html/`.
