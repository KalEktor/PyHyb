# -*- coding: utf-8 -*-
"""
PyHyB Terminal CLI & Interactive Menu Launcher
----------------------------------------------
A cross-platform menu launcher and CLI for PyHyB.
Allows users to launch the Streamlit Web GUI, run any of the three benchmark
examples, run the test suite, run the interactive builder, or build structures
directly using terminal command-line arguments (CLI mode).
"""

# pylint: disable=broad-exception-caught

import sys
import os
import argparse
import subprocess
from pathlib import Path
import unittest

# Setup path resolution for local module imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pyhyb.core.runner import run_build_hybrid
except ImportError as e:
    print(f"Error: Could not import pyhyb. {e}")
    print("Ensure the package is installed and all dependencies are available.")
    sys.exit(1)


def clear_screen():
    """Clears the console screen across Windows and Unix platforms."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Prints a beautiful ASCII art banner for PyHyB."""
    banner = """
============================================================
 ██████╗ ██╗   ██╗██╗  ██╗██╗   ██╗██████╗ 
 ██╔══██╗╚██╗ ██╔╝██║  ██║╚██╗ ██╔╝██╔══██╗
 ██████╔╝ ╚████╔╝ ███████║ ╚████╔╝ ██████╔╝
 ██╔═══╝   ╚██╔╝  ██╔══██║  ╚██╔╝  ██╔══██╗
 ██║        ██║   ██║  ██║   ██║   ██████╔╝
 ╚═╝        ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═════╝ 
 🧬 Hybrid Material Builder Launcher (v0.0.9)
============================================================
"""
    print(banner)


def run_example_1():
    """Executes Example 1: Glycine on Graphene."""
    clear_screen()
    show_banner()
    print("🧪 Running Example 1: Glycine on Graphene Substrate...")
    print("------------------------------------------------------------")

    glycine_path = PROJECT_ROOT / "example" / "data" / "glycine.xyz"
    graphene_path = PROJECT_ROOT / "example" / "data" / "graphene_7x7.cif"
    out_dir = PROJECT_ROOT / "example" / "output" / "example1_glycine"

    print(f"Material:  {glycine_path.name}")
    print(f"Substrate: {graphene_path.name}")
    print(f"Output:    {out_dir.relative_to(PROJECT_ROOT)}")
    print("Processing...")

    try:
        msg = run_build_hybrid(
            material_path=str(glycine_path),
            substrate_path=str(graphene_path),
            output_dir=str(out_dir),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5
        )
        print("\n🎉 Success! Example 1 completed successfully.")
        print(f"Details:\n{msg}")
    except Exception as e:
        print(f"\n❌ Error running Example 1: {e}", file=sys.stderr)

    print("\nPress Enter to return to the menu...")
    input()


def run_example_2():
    """Executes Example 2: Crown Ether on Graphene."""
    clear_screen()
    show_banner()
    print("🍩 Running Example 2: Crown Ether on Graphene Substrate...")
    print("------------------------------------------------------------")

    crown_path = PROJECT_ROOT / "example" / "data" / "crown_ether.xyz"
    graphene_path = PROJECT_ROOT / "example" / "data" / "graphene_7x7.cif"
    out_dir = PROJECT_ROOT / "example" / "output" / "example2_crown_ether"

    print(f"Material:  {crown_path.name}")
    print(f"Substrate: {graphene_path.name}")
    print(f"Output:    {out_dir.relative_to(PROJECT_ROOT)}")
    print("Processing...")

    try:
        msg = run_build_hybrid(
            material_path=str(crown_path),
            substrate_path=str(graphene_path),
            output_dir=str(out_dir),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5
        )
        print("\n🎉 Success! Example 2 completed successfully.")
        print(f"Details:\n{msg}")
    except Exception as e:
        print(f"\n❌ Error running Example 2: {e}", file=sys.stderr)

    print("\nPress Enter to return to the menu...")
    input()


def run_example_3():
    """Executes Example 3: Cucurbituril on Graphene Oxide."""
    clear_screen()
    show_banner()
    print("🛡️ Running Example 3: Cucurbituril on Graphene Oxide Substrate...")
    print("------------------------------------------------------------")

    cucurbit_path = PROJECT_ROOT / "example" / "data" / "cucurbituril.xyz"
    graphene_oxide_path = PROJECT_ROOT / "example" / "data" / "graphene_oxide.cif"
    out_dir = PROJECT_ROOT / "example" / "output" / "example3_cucurbituril"

    print(f"Material:  {cucurbit_path.name}")
    print(f"Substrate: {graphene_oxide_path.name}")
    print(f"Output:    {out_dir.relative_to(PROJECT_ROOT)}")
    print("Processing...")

    try:
        msg = run_build_hybrid(
            material_path=str(cucurbit_path),
            substrate_path=str(graphene_oxide_path),
            output_dir=str(out_dir),
            placement="surface",
            distance=3.0,
            collision_threshold=1.5
        )
        print("\n🎉 Success! Example 3 completed successfully.")
        print(f"Details:\n{msg}")
    except Exception as e:
        print(f"\n❌ Error running Example 3: {e}", file=sys.stderr)

    print("\nPress Enter to return to the menu...")
    input()


def launch_web_gui():
    """Spawns the Streamlit web application dashboard."""
    clear_screen()
    show_banner()
    print("🚀 Launching the Interactive Web GUI in your browser...")
    print("Streamlit will automatically open http://localhost:8501")
    print("Press Ctrl+C in this terminal when you want to stop the server.")
    print("------------------------------------------------------------")

    try:
        # Launch Streamlit as a subprocess
        subprocess.run(["streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nStopping Web Server...")
    except FileNotFoundError:
        print("\n❌ Error: Streamlit is not installed or not in PATH.", file=sys.stderr)
        print("Please check your virtual environment setup.", file=sys.stderr)
        print("\nPress Enter to return to the menu...")
        input()
    except Exception as e:
        print(f"\n❌ Error launching Streamlit: {e}", file=sys.stderr)
        print("\nPress Enter to return to the menu...")
        input()


def run_unit_tests():
    """Discovers and runs unit tests."""
    clear_screen()
    show_banner()
    print("🧪 Running PyHyB Test Suite...")
    print("------------------------------------------------------------")

    try:
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(PROJECT_ROOT / 'tests'))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        if result.wasSuccessful():
            print("\n🎉 All unit tests passed!")
        else:
            print("\n❌ Some unit tests failed.", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ Error executing unit tests: {e}", file=sys.stderr)

    print("\nPress Enter to return to the menu...")
    input()


# pylint: disable=too-many-branches,too-many-statements
def run_interactive_builder():
    """
    Interactively prompts the user for custom inputs and parameters
    to build a hybrid structure.
    """
    clear_screen()
    show_banner()
    print("🔨 Interactive Custom Hybrid Material Builder")
    print("------------------------------------------------------------")

    # 1. Inputs
    mat_path = input("Enter path to macromolecule (.xyz) (e.g. example/data/glycine.xyz): ").strip()
    if not mat_path:
        print("\n❌ Error: Macromolecule path cannot be empty.")
        print("Press Enter to return...")
        input()
        return

    sub_path = input(
        "Enter path to periodic substrate (.cif) (e.g. "
        "example/data/graphene_7x7.cif): "
    ).strip()
    if not sub_path:
        print("\n❌ Error: Substrate path cannot be empty.")
        print("Press Enter to return...")
        input()
        return

    # Resolve paths
    mat_p = Path(mat_path)
    sub_p = Path(sub_path)

    if not mat_p.exists():
        print(f"\n❌ Error: Macromolecule file does not exist: {mat_p}")
        print("Press Enter to return...")
        input()
        return

    if not sub_p.exists():
        print(f"\n❌ Error: Substrate file does not exist: {sub_p}")
        print("Press Enter to return...")
        input()
        return

    # 2. Parameters
    placement = input(
        "Enter placement logic [center / surface] (default: center): "
    ).strip().lower()
    if placement not in ["center", "surface"]:
        placement = "center"

    distance_str = input("Enter starting height in Å (default: 3.0): ").strip()
    try:
        distance = float(distance_str) if distance_str else 3.0
    except ValueError:
        distance = 3.0

    threshold_str = input("Enter collision threshold in Å (default: 1.5): ").strip()
    try:
        collision_threshold = float(threshold_str) if threshold_str else 1.5
    except ValueError:
        collision_threshold = 1.5

    rot_str = input(
        "Enter rotation angles X Y Z in degrees (default: None, e.g. 90 0 "
        "180): "
    ).strip()
    rotation = None
    if rot_str:
        try:
            rotation = [float(x) for x in rot_str.split()]
            if len(rotation) != 3:
                rotation = None
        except ValueError:
            rotation = None

    prefix = input("Enter custom output filename prefix (default: hybrid_structure): ").strip()
    if not prefix:
        prefix = "hybrid_structure"

    out_dir = input("Enter destination folder for outputs (default: output/): ").strip()
    if not out_dir:
        out_dir = str(PROJECT_ROOT / "output")

    print("\nProcessing structural combination & checks...")
    try:
        msg = run_build_hybrid(
            material_path=str(mat_p),
            substrate_path=str(sub_p),
            output_dir=out_dir,
            placement=placement,
            distance=distance,
            collision_threshold=collision_threshold,
            rotation=rotation,
            prefix=prefix
        )
        print("\n🎉 Success! Custom hybrid structure built successfully.")
        print(f"Details:\n{msg}")
    except Exception as e:
        print(f"\n❌ Error building hybrid structure: {e}", file=sys.stderr)

    print("\nPress Enter to return to the menu...")
    input()


def parse_cli_args():
    """Parses command-line arguments for direct, non-interactive terminal launcher execution."""
    parser = argparse.ArgumentParser(
        description=(
            "PyHyB Terminal CLI Launcher for direct non-interactive creation "
            "of hybrid structures."
        )
    )
    parser.add_argument(
        "-m", "--material",
        help="Path to macromolecule .xyz structure file"
    )
    parser.add_argument(
        "-s", "--substrate",
        help="Path to periodic substrate .cif structure file"
    )
    parser.add_argument(
        "-o", "--outdir",
        default=str(PROJECT_ROOT / "output"),
        help="Output directory for generated structures (default: output/)"
    )
    parser.add_argument(
        "-p", "--placement",
        choices=["center", "surface"],
        default="center",
        help="Macromolecule placement logic (default: center)"
    )
    parser.add_argument(
        "-d", "--distance",
        type=float,
        default=3.0,
        help="Starting vertical separation distance in Å (default: 3.0)"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=1.5,
        help="Collision detection threshold in Å (default: 1.5)"
    )
    parser.add_argument(
        "-r", "--rotation",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        help="3D Euler rotation angles in degrees (e.g. 90 0 180)"
    )
    parser.add_argument(
        "--prefix",
        default="hybrid_structure",
        help="Filename prefix for generated structures (default: hybrid_structure)"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Trigger DFTB+ geometric optimization of the combined structure"
    )

    # We only activate CLI mode if material and substrate arguments are provided
    if len(sys.argv) > 1:
        return parser.parse_args()
    return None


def main():
    """Main menu display loop."""
    while True:
        clear_screen()
        show_banner()

        print("Please select an option:")
        print(" 1) Launch PyHyB 3D Web Application GUI 🚀")
        print(" 2) Run Custom Interactive Hybrid Builder 🔨")
        print(" 3) Run Example 1 (Glycine deposition on Graphene) 🧪")
        print(" 4) Run Example 2 (Crown Ether deposition on Graphene) 🍩")
        print(" 5) Run Example 3 (Cucurbituril deposition on Graphene Oxide) 🛡️")
        print(" 6) Run Unit Tests 🧪")
        print(" 7) Exit 🚪")
        print("------------------------------------------------------------")

        choice = input("Enter choice [1-7]: ").strip()

        if choice == '1':
            launch_web_gui()
        elif choice == '2':
            run_interactive_builder()
        elif choice == '3':
            run_example_1()
        elif choice == '4':
            run_example_2()
        elif choice == '5':
            run_example_3()
        elif choice == '6':
            run_unit_tests()
        elif choice == '7':
            clear_screen()
            print("Thank you for using PyHyB! Goodbye.")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please press Enter and select a valid option...")
            input()


def bootstrap():
    """Handles parsing CLI arguments or launching the interactive main menu."""
    args = parse_cli_args()
    if args and args.material and args.substrate:
        # CLI direct non-interactive launcher creation of hybrid structures
        print("🔧 PyHyB CLI hybrid structure builder initiated...")
        print(f"Material:  {args.material}")
        print(f"Substrate: {args.substrate}")
        print(f"Output:    {args.outdir}/{args.prefix}.*")
        try:
            msg = run_build_hybrid(
                material_path=args.material,
                substrate_path=args.substrate,
                output_dir=args.outdir,
                placement=args.placement,
                distance=args.distance,
                collision_threshold=args.threshold,
                rotation=args.rotation,
                prefix=args.prefix,
                optimize=args.optimize
            )
            print("\n🎉 Success! Hybrid structure built.")
            print(msg)
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error building hybrid structure: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Launch interactive console TUI menu
        try:
            main()
        except KeyboardInterrupt:
            print("\nExiting Launcher...")
            sys.exit(0)


if __name__ == '__main__':
    bootstrap()
