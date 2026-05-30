PyHyB API Documentation
=======================

.. toctree::
   :maxdepth: 2
   :caption: Contents

   api/builder
   api/runner
   api/hybrid_runner
   api/optimizer
   api/tools
   api/cross_tools
   api/inout

Overview
--------

PyHyB is a high-performance hybrid molecular/substrate structure
builder for computational chemistry. It deposits macromolecules
(`.xyz`) onto periodic substrates (`.cif`) using intelligent
placement algorithms.

Quick Start
-----------

.. code-block:: python

   from pyhyb.core.runner import run_build_hybrid

   msg = run_build_hybrid(
       material_path="glycine.xyz",
       substrate_path="graphene_7x7.cif",
       output_dir="output/",
       placement="surface",
       distance=3.0,
   )

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
