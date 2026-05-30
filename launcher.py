# -*- coding: utf-8 -*-
"""
PyHyB Terminal CLI & Interactive Menu Launcher.

A cross-platform menu launcher and CLI for PyHyB.
Allows users to launch the Streamlit Web GUI, run benchmark
examples, run the test suite, run the interactive builder,
or build structures directly using CLI arguments.
"""

# pylint: disable=broad-exception-caught

import argparse
import os
import subprocess
import sys
import unittest
from pathlib import Path

# Setup path resolution for local module imports
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pyhyb.core.runner import run_build_hybrid
    from pyhyb.tools.builder import HybridConfig
except ImportError as e:
    print(f"Error: Could not import pyhyb. {e}")
    print(
        "Ensure the package is installed and all "
        "dependencies are available."
    )
    sys.exit(1)

_DEFAULTS = HybridConfig.defaults()


def clear_screen():
    """Clear the console screen (cross-platform)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Print the ASCII art banner for PyHyB."""
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
    """Execute Example 1: Glycine on Graphene."""
    clear_screen()
    show_banner()
    print(
        "🧪 Running Example 1: Glycine on Graphene "
        "Substrate..."
    )
    print("-" * 60)

    glycine = (
        PROJECT_ROOT / "example" / "data" / "glycine.xyz"
    )
    graphene = (
        PROJECT_ROOT / "example" / "data"
        / "graphene_7x7.cif"
    )
    out_dir = (
        PROJECT_ROOT / "example" / "output"
        / "example1_glycine"
    )

    print(f"Material:  {glycine.name}")
    print(f"Substrate: {graphene.name}")
    print(f"Output:    {out_dir.relative_to(PROJECT_ROOT)}")
    print("Processing...")

    try:
        msg = run_build_hybrid(
            material_path=str(glycine),
            substrate_path=str(graphene),
            output_dir=str(out_dir),
            placement="surface",
            distance=_DEFAULTS["distance"],
            collision_threshold=(
                _DEFAULTS["collision_threshold"]
            ),
        )
        print("\n🎉 Success! Example 1 completed.")
        print(f"Details:\n{msg}")
    except Exception as exc:
        print(
            f"\n❌ Error running Example 1: {exc}",
            file=sys.stderr,
        )

    print("\nPress Enter to return to the menu...")
    input()


def run_example_2():
    """Execute Example 2: Crown Ether on Graphene."""
    clear_screen()
    show_banner()
    print(
        "🍩 Running Example 2: Crown Ether on "
        "Graphene Substrate..."
    )
    print("-" * 60)

    crown = (
        PROJECT_ROOT / "example" / "data"
        / "crown_ether.xyz"
    )
    graphene = (
        PROJECT_ROOT / "example" / "data"
        / "graphene_7x7.cif"
    )
    out_dir = (
        PROJECT_ROOT / "example" / "output"
        / "example2_crown_ether"
    )

    print(f"Material:  {crown.name}")
    print(f"Substrate: {graphene.name}")
    print(f"Output:    {out_dir.relative_to(PROJECT_ROOT)}")
    print("Processing...")

    try:
        msg = run_build_hybrid(
            material_path=str(crown),
            substrate_path=str(graphene),
            output_dir=str(out_dir),
            placement="surface",
            distance=_DEFAULTS["distance"],
            collision_threshold=(
                _DEFAULTS["collision_threshold"]
            ),
        )
        print("\n🎉 Success! Example 2 completed.")
        print(f"Details:\n{msg}")
    except Exception as exc:
        print(
            f"\n❌ Error running Example 2: {exc}",
            file=sys.stderr,
        )

    print("\nPress Enter to return to the menu...")
    input()


def run_example_3():
    """Execute Example 3: Cucurbituril on Graphene Oxide."""
    clear_screen()
    show_banner()
    print(
        "🛡️ Running Example 3: Cucurbituril on "
        "Graphene Oxide Substrate..."
    )
    print("-" * 60)

    cucurbit = (
        PROJECT_ROOT / "example" / "data"
        / "cucurbituril.xyz"
    )
    graphene_oxide = (
        PROJECT_ROOT / "example" / "data"
        / "graphene_oxide.cif"
    )
    out_dir = (
        PROJECT_ROOT / "example" / "output"
        / "example3_cucurbituril"
    )

    print(f"Material:  {cucurbit.name}")
    print(f"Substrate: {graphene_oxide.name}")
    print(f"Output:    {out_dir.relative_to(PROJECT_ROOT)}")
    print("Processing...")

    try:
        msg = run_build_hybrid(
            material_path=str(cucurbit),
            substrate_path=str(graphene_oxide),
            output_dir=str(out_dir),
            placement="surface",
            distance=_DEFAULTS["distance"],
            collision_threshold=(
                _DEFAULTS["collision_threshold"]
            ),
        )
        print("\n🎉 Success! Example 3 completed.")
        print(f"Details:\n{msg}")
    except Exception as exc:
        print(
            f"\n❌ Error running Example 3: {exc}",
            file=sys.stderr,
        )

    print("\nPress Enter to return to the menu...")
    input()


def launch_web_gui():
    """Spawn the Streamlit web application dashboard."""
    clear_screen()
    show_banner()
    print(
        "🚀 Launching the Interactive Web GUI "
        "in your browser..."
    )
    print(
        "Streamlit will automatically open "
        "http://localhost:8501"
    )
    print(
        "Press Ctrl+C in this terminal when you "
        "want to stop the server."
    )
    print("-" * 60)

    try:
        subprocess.run(
            ["streamlit", "run", "app.py"], check=True
        )
    except KeyboardInterrupt:
        print("\nStopping Web Server...")
    except FileNotFoundError:
        print(
            "\n❌ Error: Streamlit is not installed or "
            "not in PATH.",
            file=sys.stderr,
        )
        print(
            "Please check your virtual environment setup.",
            file=sys.stderr,
        )
        print("\nPress Enter to return to the menu...")
        input()
    except Exception as exc:
        print(
            f"\n❌ Error launching Streamlit: {exc}",
            file=sys.stderr,
        )
        print("\nPress Enter to return to the menu...")
        input()


def run_unit_tests():
    """Discover and run unit tests."""
    clear_screen()
    show_banner()
    print("🧪 Running PyHyB Test Suite...")
    print("-" * 60)

    try:
        loader = unittest.TestLoader()
        suite = loader.discover(
            start_dir=str(PROJECT_ROOT / 'tests')
        )
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        if result.wasSuccessful():
            print("\n🎉 All unit tests passed!")
        else:
            print(
                "\n❌ Some unit tests failed.",
                file=sys.stderr,
            )
    except Exception as exc:
        print(
            f"\n❌ Error executing unit tests: {exc}",
            file=sys.stderr,
        )

    print("\nPress Enter to return to the menu...")
    input()


# pylint: disable=too-many-branches,too-many-statements
def run_interactive_builder():
    """Prompt the user for custom inputs and build."""
    clear_screen()
    show_banner()
    print("🔨 Interactive Custom Hybrid Material Builder")
    print("-" * 60)

    # 1. Inputs
    mat_path = input(
        "Enter path to macromolecule (.xyz) "
        "(e.g. example/data/glycine.xyz): "
    ).strip()
    if not mat_path:
        print("\n❌ Error: Macromolecule path is empty.")
        print("Press Enter to return...")
        input()
        return

    sub_path = input(
        "Enter path to periodic substrate (.cif) "
        "(e.g. example/data/graphene_7x7.cif): "
    ).strip()
    if not sub_path:
        print("\n❌ Error: Substrate path is empty.")
        print("Press Enter to return...")
        input()
        return

    mat_p = Path(mat_path)
    sub_p = Path(sub_path)

    if not mat_p.exists():
        print(
            f"\n❌ Error: Macromolecule file does "
            f"not exist: {mat_p}"
        )
        print("Press Enter to return...")
        input()
        return

    if not sub_p.exists():
        print(
            f"\n❌ Error: Substrate file does "
            f"not exist: {sub_p}"
        )
        print("Press Enter to return...")
        input()
        return

    # 2. Parameters
    placement = input(
        "Enter placement logic [center / surface] "
        "(default: center): "
    ).strip().lower()
    if placement not in ["center", "surface"]:
        placement = _DEFAULTS["placement"]

    distance_str = input(
        "Enter starting height in Å "
        f"(default: {_DEFAULTS['distance']}): "
    ).strip()
    try:
        distance = (
            float(distance_str)
            if distance_str
            else _DEFAULTS["distance"]
        )
    except ValueError:
        distance = _DEFAULTS["distance"]

    threshold_str = input(
        "Enter collision threshold in Å "
        f"(default: {_DEFAULTS['collision_threshold']}): "
    ).strip()
    try:
        collision_threshold = (
            float(threshold_str)
            if threshold_str
            else _DEFAULTS["collision_threshold"]
        )
    except ValueError:
        collision_threshold = (
            _DEFAULTS["collision_threshold"]
        )

    rot_str = input(
        "Enter rotation angles X Y Z in degrees "
        "(default: None, e.g. 90 0 180): "
    ).strip()
    rotation = None
    if rot_str:
        try:
            rotation = [
                float(x) for x in rot_str.split()
            ]
            if len(rotation) != 3:
                rotation = None
        except ValueError:
            rotation = None

    prefix = input(
        "Enter custom output filename prefix "
        "(default: hybrid_structure): "
    ).strip()
    if not prefix:
        prefix = "hybrid_structure"

    out_dir = input(
        "Enter destination folder for outputs "
        "(default: output/): "
    ).strip()
    if not out_dir:
        out_dir = str(PROJECT_ROOT / "output")

    print(
        "\nProcessing structural combination & checks..."
    )
    try:
        msg = run_build_hybrid(
            material_path=str(mat_p),
            substrate_path=str(sub_p),
            output_dir=out_dir,
            placement=placement,
            distance=distance,
            collision_threshold=collision_threshold,
            rotation=rotation,
            prefix=prefix,
        )
        print(
            "\n🎉 Success! Custom hybrid structure "
            "built successfully."
        )
        print(f"Details:\n{msg}")
    except Exception as exc:
        print(
            f"\n❌ Error building hybrid structure: {exc}",
            file=sys.stderr,
        )

    print("\nPress Enter to return to the menu...")
    input()


def parse_cli_args():
    """Parse arguments for non-interactive CLI mode.

    Returns:
        argparse.Namespace or None: Parsed args when CLI
        arguments are present, ``None`` otherwise.
    """
    parser = argparse.ArgumentParser(
        description=(
            "PyHyB Terminal CLI Launcher for direct "
            "non-interactive creation of hybrid "
            "structures."
        )
    )
    parser.add_argument(
        "-m", "--material",
        help="Path to macromolecule .xyz file",
    )
    parser.add_argument(
        "-s", "--substrate",
        help="Path to substrate .cif file",
    )
    parser.add_argument(
        "-o", "--outdir",
        default=str(PROJECT_ROOT / "output"),
        help="Output directory (default: output/)",
    )
    parser.add_argument(
        "-p", "--placement",
        choices=["center", "surface"],
        default=_DEFAULTS["placement"],
        help="Placement logic (default: center)",
    )
    parser.add_argument(
        "-d", "--distance",
        type=float,
        default=_DEFAULTS["distance"],
        help="Vertical separation in Å (default: 3.0)",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=_DEFAULTS["collision_threshold"],
        help="Collision threshold in Å (default: 1.5)",
    )
    parser.add_argument(
        "-r", "--rotation",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        help="Euler rotation angles (degrees)",
    )
    parser.add_argument(
        "--prefix",
        default="hybrid_structure",
        help="Filename prefix (default: hybrid_structure)",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Trigger DFTB+ geometric optimization",
    )

    if len(sys.argv) > 1:
        return parser.parse_args()
    return None


def main():
    """Main menu display loop."""
    while True:
        clear_screen()
        show_banner()

        print("Please select an option:")
        print(" 1) Launch PyHyB 3D Web App GUI 🚀")
        print(" 2) Run Custom Interactive Builder 🔨")
        print(" 3) Run Example 1 (Glycine on Graphene) 🧪")
        print(
            " 4) Run Example 2 "
            "(Crown Ether on Graphene) 🍩"
        )
        print(
            " 5) Run Example 3 "
            "(Cucurbituril on Graphene Oxide) 🛡️"
        )
        print(" 6) Run Unit Tests 🧪")
        print(" 7) Exit 🚪")
        print("-" * 60)

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
            print(
                "\nInvalid choice. "
                "Press Enter and select a valid option..."
            )
            input()


def bootstrap():
    """Handle CLI arguments or launch interactive menu."""
    args = parse_cli_args()
    if args and args.material and args.substrate:
        print(
            "🔧 PyHyB CLI hybrid structure builder "
            "initiated..."
        )
        print(f"Material:  {args.material}")
        print(f"Substrate: {args.substrate}")
        print(
            f"Output:    {args.outdir}/{args.prefix}.*"
        )
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
                optimize=args.optimize,
            )
            print("\n🎉 Success! Hybrid structure built.")
            print(msg)
            sys.exit(0)
        except Exception as exc:
            print(
                f"\n❌ Error building hybrid structure: "
                f"{exc}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        try:
            main()
        except KeyboardInterrupt:
            print("\nExiting Launcher...")
            sys.exit(0)


if __name__ == '__main__':
    bootstrap()
