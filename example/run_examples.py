# -*- coding: utf-8 -*-
"""
PyHyB Examples Runner
---------------------
This script executes two separate independent examples to verify
the hybrid material building capability of PyHyB:

1. Depositing glycine (amino acid) on a 7x7 graphene unit cell.
2. Depositing a 15-crown-5 macrocycle (crown ether) on a 7x7 graphene unit cell.
"""
from pathlib import Path
import sys

# Setup paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# pylint: disable=wrong-import-position
from pyhyb.core.runner import run_build_hybrid


def main():
    """
    Executes the glycine and crown ether on graphene hybrid construction examples.
    """
    print("==================================================")
    print("            PyHyB Examples Runner")
    print("==================================================")

    glycine_path = PROJECT_ROOT / "example" / "data" / "glycine.xyz"
    crown_path = PROJECT_ROOT / "example" / "data" / "crown_ether.xyz"
    cucurbit_path = PROJECT_ROOT / "example" / "data" / "cucurbituril.xyz"
    graphene_path = PROJECT_ROOT / "example" / "data" / "graphene_7x7.cif"
    graphene_oxide_path = PROJECT_ROOT / "example" / "data" / "graphene_oxide.cif"

    # 1. Glycine on 7x7 Graphene
    print("\n--- Running Example 1: Glycine on 7x7 Graphene ---")
    try:
        msg1 = run_build_hybrid(
            material_path=str(glycine_path),
            substrate_path=str(graphene_path),
            output_dir=str(PROJECT_ROOT / "example" / "output" / "example1_glycine"),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5
        )
        print("Example 1 Completed Successfully!")
        print(msg1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Example 1 Failed: {e}")

    # 2. Crown Ether on 7x7 Graphene
    print("\n--- Running Example 2: Crown Ether on 7x7 Graphene ---")
    try:
        msg2 = run_build_hybrid(
            material_path=str(crown_path),
            substrate_path=str(graphene_path),
            output_dir=str(PROJECT_ROOT / "example" / "output" / "example2_crown_ether"),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5
        )
        print("Example 2 Completed Successfully!")
        print(msg2)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Example 2 Failed: {e}")

    # 3. Cucurbituril on 7x7 Graphene Oxide
    print("\n--- Running Example 3: Cucurbituril on Graphene Oxide ---")
    try:
        msg3 = run_build_hybrid(
            material_path=str(cucurbit_path),
            substrate_path=str(graphene_oxide_path),
            output_dir=str(PROJECT_ROOT / "example" / "output" / "example3_cucurbituril"),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5
        )
        print("Example 3 Completed Successfully!")
        print(msg3)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Example 3 Failed: {e}")

    print("\n==================================================")
    print("All examples executed. View outputs in example/output/ folder.")
    print("==================================================")


if __name__ == '__main__':
    main()
