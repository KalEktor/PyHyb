# -*- coding: utf-8 -*-
"""
PyHyB Examples Runner.

Executes three independent examples to verify the hybrid
material building capability of PyHyB:

1. Depositing glycine on a 7x7 graphene unit cell.
2. Depositing a 15-crown-5 macrocycle on graphene.
3. Depositing cucurbituril on graphene oxide.
"""
from pathlib import Path
import sys

# Setup paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# pylint: disable=wrong-import-position
from pyhyb.core.runner import run_build_hybrid


DATA_DIR = PROJECT_ROOT / "example" / "data"
OUT_DIR = PROJECT_ROOT / "example" / "output"


def main():
    """Run all three benchmark examples."""
    print("=" * 50)
    print("            PyHyB Examples Runner")
    print("=" * 50)

    glycine = DATA_DIR / "glycine.xyz"
    crown = DATA_DIR / "crown_ether.xyz"
    cucurbit = DATA_DIR / "cucurbituril.xyz"
    graphene = DATA_DIR / "graphene_7x7.cif"
    graphene_oxide = DATA_DIR / "graphene_oxide.cif"

    # 1. Glycine on 7x7 Graphene
    print(
        "\n--- Example 1: Glycine on Graphene ---"
    )
    try:
        msg1 = run_build_hybrid(
            material_path=str(glycine),
            substrate_path=str(graphene),
            output_dir=str(
                OUT_DIR / "example1_glycine"
            ),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5,
        )
        print("Example 1 Completed Successfully!")
        print(msg1)
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        print(f"Example 1 Failed: {exc}")

    # 2. Crown Ether on 7x7 Graphene
    print(
        "\n--- Example 2: Crown Ether on Graphene ---"
    )
    try:
        msg2 = run_build_hybrid(
            material_path=str(crown),
            substrate_path=str(graphene),
            output_dir=str(
                OUT_DIR / "example2_crown_ether"
            ),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5,
        )
        print("Example 2 Completed Successfully!")
        print(msg2)
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        print(f"Example 2 Failed: {exc}")

    # 3. Cucurbituril on Graphene Oxide
    print(
        "\n--- Example 3: Cucurbituril on GO ---"
    )
    try:
        msg3 = run_build_hybrid(
            material_path=str(cucurbit),
            substrate_path=str(graphene_oxide),
            output_dir=str(
                OUT_DIR / "example3_cucurbituril"
            ),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5,
        )
        print("Example 3 Completed Successfully!")
        print(msg3)
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        print(f"Example 3 Failed: {exc}")

    print("\n" + "=" * 50)
    print(
        "All examples executed. View outputs in "
        "example/output/ folder."
    )
    print("=" * 50)


if __name__ == '__main__':
    main()
