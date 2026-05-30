# -*- coding: utf-8 -*-
"""
Sphinx configuration for PyHyB API documentation.

Auto-generates API reference from inline docstrings and
type annotations using ``sphinx.ext.autodoc`` and
``sphinx.ext.napoleon``.
"""
import sys
from pathlib import Path

# -- Path setup ------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

# -- Project information ---------------------------------------
project = 'PyHyB'
author = 'Konstantinos Alektoridis'
copyright = '2026, Konstantinos Alektoridis'  # noqa: A001
release = '0.0.9.dev0'

# -- General configuration ------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstrings = True
napoleon_numpy_docstrings = False
napoleon_include_init_with_doc = True

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}

# Intersphinx mappings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'ase': ('https://wiki.fysik.dtu.dk/ase/', None),
}

# -- Options for HTML output -----------------------------------
html_theme = 'alabaster'
html_theme_options = {
    'description': (
        'Hybrid molecular/substrate structure builder'
    ),
    'github_user': 'KalEktor',
    'github_repo': 'PyHyB',
    'github_button': True,
}

# Exclude test and example modules
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
