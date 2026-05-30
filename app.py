# -*- coding: utf-8 -*-
"""
PyHyB Streamlit Web Interface.

A visually stunning, interactive web application to construct
hybrid configurations by combining molecular structures
(.xyz) with periodic substrates (.cif) in 3D.
"""

import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from ase.io import read

from pyhyb.core.hybrid_runner import HybridWorkflowRunner
from pyhyb.tools.builder import HybridConfig

PROJECT_ROOT = Path(__file__).resolve().parent
_DEFAULTS = HybridConfig.defaults()


def render_3d_molecule(
    struct_text: str,
    file_format: str = "xyz",
    height: int = 400,
):
    """Render a structure using py3Dmol.js via iframe.

    Args:
        struct_text: Raw file content as a string.
        file_format: One of ``'xyz'`` or ``'cif'``.
        height: Iframe height in pixels.
    """
    safe = (
        struct_text
        .replace("`", "\\`")
        .replace("\n", "\\n")
        .replace("\r", "")
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html, body {{
                margin: 0; padding: 0;
                width: 100%; height: 100%;
                overflow: hidden;
                background-color: #0f172a;
            }}
            #container-3d {{
                width: 100%; height: 100%;
                position: relative;
            }}
            .viewer-label {{
                position: absolute;
                top: 10px; left: 10px;
                background: rgba(15, 23, 42, 0.85);
                color: #f8fafc;
                padding: 4px 10px;
                border-radius: 6px;
                font-family: sans-serif;
                font-size: 12px;
                z-index: 10;
                pointer-events: none;
                border: 1px solid rgba(255,255,255,0.1);
            }}
        </style>
        <script src=
          "https://3dmol.org/build/3Dmol-min.js"></script>
    </head>
    <body>
        <div class="viewer-label">
            {file_format.upper()} Viewer
            (Drag to rotate, Scroll to zoom)
        </div>
        <div id="container-3d"></div>
        <script>
            document.addEventListener(
              "DOMContentLoaded", function() {{
                let el = document.getElementById(
                  "container-3d");
                let v = $3Dmol.createViewer(
                  el, {{ backgroundColor: '#0f172a' }});
                let data = `{safe}`;
                v.addModel(data, "{file_format}");
                v.setStyle({{}}, {{
                    sphere: {{
                      scale: 0.28,
                      colorscheme: 'Jmol'
                    }},
                    stick: {{
                      radius: 0.08,
                      colorscheme: 'Jmol'
                    }}
                }});
                if ("{file_format}" === "cif") {{
                    v.addUnitCell();
                }}
                v.zoomTo();
                v.render();
            }});
        </script>
    </body>
    </html>
    """
    components.html(html, height=height)


# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def main():
    """Main function containing all Streamlit page logic."""
    st.set_page_config(
        page_title="PyHyB: Hybrid Material Builder",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Premium Font and Custom Styling
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2'
        "?family=Inter:wght@300;400;500;600;700"
        "&family=Outfit:wght@400;500;600;700;800"
        '&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(_css_block(), unsafe_allow_html=True)
    st.markdown(_banner_block(), unsafe_allow_html=True)

    # Sidebar
    (
        placement,
        distance,
        collision_threshold,
        rotation_args,
        prefix_val,
        prefix_arg,
        optimize,
        fmax,
        steps,
    ) = _sidebar_controls()

    # File upload columns
    col_inputs, col_vis = st.columns([1, 1])

    with col_inputs:
        _upload_section()

    with col_vis:
        _preview_section()

    # Execution and outputs
    st.markdown(
        "<br><hr>", unsafe_allow_html=True
    )
    st.subheader("🚀 3. Construct Hybrid Material")

    mat = st.session_state.material_content
    sub = st.session_state.substrate_content
    if not mat or not sub:
        st.warning(
            "Please upload both a macromolecule (.xyz) "
            "and substrate (.cif) above to continue."
        )
    else:
        _build_section(
            placement,
            distance,
            collision_threshold,
            rotation_args,
            prefix_val,
            prefix_arg,
            optimize,
            fmax,
            steps,
        )


# ----------------------------------------------------------
# UI helper functions
# ----------------------------------------------------------

def _css_block() -> str:
    """Return the CSS styling block."""
    return """
    <style>
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 20px -2px rgba(0,0,0,0.15);
            margin-bottom: 1rem;
            transition: all 0.25s
                cubic-bezier(0.4, 0, 0.2, 1);
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 25px -4px rgba(0,0,0,0.25);
            border-color: rgba(63, 131, 248, 0.4);
        }
        .stat-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
            font-weight: 600;
            margin-bottom: 0.4rem;
        }
        .stat-value {
            font-size: 2rem; font-weight: 800;
            background: linear-gradient(
                135deg, #60a5fa 0%, #34d399 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'Outfit', sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color: #0f172a;
            color: #f8fafc;
            border-right: 1px solid #1e293b;
        }
        [data-testid="stSidebar"]
          [data-testid="stMarkdownContainer"] p {
            color: #94a3b8;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }
    </style>
    """


def _banner_block() -> str:
    """Return the header banner HTML."""
    return (
        '<div style="background-color: #0f172a; '
        "padding: 2rem; border-radius: 18px; "
        "margin-bottom: 2rem; "
        "border: 1px solid #1e293b; "
        "box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4); "
        'text-align: center;">'
        '<h1 style="margin: 0; font-size: 3.5rem; '
        "font-weight: 800; "
        "background: linear-gradient("
        "135deg, #60a5fa 0%, #34d399 100%); "
        "-webkit-background-clip: text; "
        "-webkit-text-fill-color: transparent; "
        "font-family: 'Outfit', sans-serif; "
        'letter-spacing: -1.5px;">PyHyB</h1>'
        '<p style="margin: 0.5rem 0 0 0; '
        "font-family: 'Inter', sans-serif; "
        "font-size: 1.1rem; color: #94a3b8; "
        "font-weight: 400; letter-spacing: 1.5px; "
        'text-transform: uppercase;">'
        "Molecular Hybrid Technology</p></div>"
    )


def _sidebar_controls():
    """Render sidebar controls and return values."""
    with st.sidebar:
        st.markdown("## ⚙️ Build Options")
        st.markdown(
            "Configure how your macromolecule will be "
            "positioned and checked on the substrate."
        )

        placement = st.selectbox(
            "Placement Logic",
            options=["center", "surface"],
            index=0,
            help=(
                "center: Centre molecule in middle of "
                "the unit cell Z space.\n"
                "surface: Place bottom of molecule "
                "target distance above the highest "
                "substrate atom."
            ),
        )

        distance = st.slider(
            "Starting Height (Å)",
            min_value=1.0,
            max_value=10.0,
            value=_DEFAULTS["distance"],
            step=0.1,
            help="Only for 'surface' placement logic.",
        )

        collision_threshold = st.slider(
            "Collision Threshold (Å)",
            min_value=0.5,
            max_value=4.0,
            value=_DEFAULTS["collision_threshold"],
            step=0.1,
            help=(
                "Minimum allowed distance between "
                "macromolecule and substrate atoms."
            ),
        )

        st.markdown("### 🔄 Molecule Rotation")
        st.markdown(
            "Pre-rotate the macromolecule around "
            "its Centre of Mass (COM) before "
            "depositing."
        )
        rot_x = st.slider(
            "Rotate X (°)", 0.0, 360.0, 0.0, step=5.0
        )
        rot_y = st.slider(
            "Rotate Y (°)", 0.0, 360.0, 0.0, step=5.0
        )
        rot_z = st.slider(
            "Rotate Z (°)", 0.0, 360.0, 0.0, step=5.0
        )

        rotation_args = (
            [rot_x, rot_y, rot_z]
            if (rot_x != 0 or rot_y != 0 or rot_z != 0)
            else None
        )

        st.markdown("### 📁 Output File Naming")
        prefix_val = st.text_input(
            "Custom File Prefix",
            value="hybrid_structure",
            help="Custom prefix name for outputs.",
        ).strip()
        prefix_arg = prefix_val if prefix_val else None

        optimize = False
        fmax = 0.05
        steps = 200

    return (
        placement, distance, collision_threshold,
        rotation_args, prefix_val, prefix_arg,
        optimize, fmax, steps,
    )


def _upload_section():
    """Render the file upload and example loading UI."""
    st.subheader("📤 1. Upload Structures")

    uploaded_material = st.file_uploader(
        "Upload Macromolecule (.xyz)",
        type=["xyz"],
        help="Select a standard molecular .xyz file.",
    )
    uploaded_substrate = st.file_uploader(
        "Upload Periodic Substrate (.cif)",
        type=["cif"],
        help="Select a periodic substrate .cif file.",
    )

    st.markdown("---")
    st.subheader("💡 Load Verification Examples")
    st.write(
        "Test PyHyB with provided benchmark structures:"
    )

    col1, col2, col3 = st.columns(3)
    data = PROJECT_ROOT / "example" / "data"

    if "material_content" not in st.session_state:
        st.session_state.material_content = None
        st.session_state.material_name = None
    if "substrate_content" not in st.session_state:
        st.session_state.substrate_content = None
        st.session_state.substrate_name = None

    if col1.button("🧬 Load Glycine on Graphene"):
        _load_example(
            data / "glycine.xyz",
            data / "graphene_7x7.cif",
            "glycine.xyz",
            "graphene_7x7.cif",
        )
        st.success("Glycine & Graphene loaded!")

    if col2.button("🍩 Load Crown Ether"):
        _load_example(
            data / "crown_ether.xyz",
            data / "graphene_7x7.cif",
            "crown_ether.xyz",
            "graphene_7x7.cif",
        )
        st.success("Crown Ether loaded!")

    if col3.button("🛡️ Load Cucurbituril"):
        _load_example(
            data / "cucurbituril.xyz",
            data / "graphene_oxide.cif",
            "cucurbituril.xyz",
            "graphene_oxide.cif",
        )
        st.success("Cucurbituril loaded!")

    if uploaded_material:
        st.session_state.material_content = (
            uploaded_material.getvalue().decode("utf-8")
        )
        st.session_state.material_name = (
            uploaded_material.name
        )
    if uploaded_substrate:
        st.session_state.substrate_content = (
            uploaded_substrate.getvalue().decode("utf-8")
        )
        st.session_state.substrate_name = (
            uploaded_substrate.name
        )


def _load_example(
    mat_path, sub_path, mat_name, sub_name
):
    """Load example data into session state.

    Args:
        mat_path: Path to the material file.
        sub_path: Path to the substrate file.
        mat_name: Display name for the material.
        sub_name: Display name for the substrate.
    """
    with open(mat_path, "r", encoding="utf-8") as fh:
        st.session_state.material_content = fh.read()
        st.session_state.material_name = mat_name
    with open(sub_path, "r", encoding="utf-8") as fh:
        st.session_state.substrate_content = fh.read()
        st.session_state.substrate_name = sub_name


def _preview_section():
    """Render the 3D structure preview panel."""
    st.subheader("👁️ 2. Structure Previews")

    mat = st.session_state.material_content
    sub = st.session_state.substrate_content

    if mat or sub:
        tab_mat, tab_sub = st.tabs([
            "Macromolecule", "Substrate"
        ])
        with tab_mat:
            if mat:
                name = st.session_state.material_name
                st.markdown(f"**Filename:** `{name}`")
                render_3d_molecule(mat, "xyz")
            else:
                st.info("No macromolecule loaded yet.")
        with tab_sub:
            if sub:
                name = st.session_state.substrate_name
                st.markdown(f"**Filename:** `{name}`")
                render_3d_molecule(sub, "cif")
            else:
                st.info("No substrate loaded yet.")
    else:
        st.info(
            "Upload files or load a verification "
            "example to preview structures in 3D."
        )


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
def _build_section(
    placement, distance, collision_threshold,
    rotation_args, prefix_val, prefix_arg,
    optimize, fmax, steps,
):
    """Handle the build button and output display."""
    if not st.button(
        "Construct Hybrid Structure 🔨",
        type="primary",
        use_container_width=True,
    ):
        return

    with st.spinner(
        "Executing PyHyB structure building..."
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            mat_file = tmp / "molecule.xyz"
            sub_file = tmp / "substrate.cif"
            out_dir = tmp / "output"
            out_dir.mkdir(exist_ok=True)

            with open(
                mat_file, "w", encoding="utf-8"
            ) as fh:
                fh.write(
                    st.session_state.material_content
                )
            with open(
                sub_file, "w", encoding="utf-8"
            ) as fh:
                fh.write(
                    st.session_state.substrate_content
                )

            runner = HybridWorkflowRunner()
            success, result_msg = runner.run(
                material_path=str(mat_file),
                substrate_path=str(sub_file),
                output_dir=str(out_dir),
                placement=placement,
                distance=distance,
                collision_threshold=collision_threshold,
                rotation=rotation_args,
                optimize=optimize,
                prefix=prefix_arg,
                fmax=fmax,
                steps=steps,
            )

            if success:
                _show_results(
                    out_dir, prefix_val, optimize,
                    result_msg,
                )
            else:
                st.error(
                    "Failed to combine structures:\n"
                    f"{result_msg}"
                )


def _show_results(
    out_dir, prefix_val, optimize, result_msg
):
    """Display build results and download buttons."""
    st.success("Hybrid structure constructed!")
    out_prefix = prefix_val or "hybrid_structure"
    sfx = "_opt" if optimize else ""
    cif = out_dir / f"{out_prefix}{sfx}.cif"
    xyz = out_dir / f"{out_prefix}{sfx}.xyz"
    gen = out_dir / f"{out_prefix}{sfx}.gen"

    col_det, col_view = st.columns([1, 1])

    with col_det:
        st.subheader("📋 Build Details")
        _stat_cards(cif)
        st.subheader("💾 Download Output Files")
        _download_buttons(cif, xyz, gen, out_prefix, sfx)
        with st.expander("📝 View Execution Log"):
            st.code(result_msg)
            log_path = out_dir / "build.log"
            if log_path.exists():
                with open(
                    log_path, "r", encoding="utf-8"
                ) as lf:
                    st.text(lf.read())

    with col_view:
        st.subheader("🔬 3D Hybrid Structure")
        if cif.exists():
            with open(
                cif, "r", encoding="utf-8"
            ) as fh:
                render_3d_molecule(
                    fh.read(), "cif", height=450
                )


def _stat_cards(cif_path):
    """Render atom count and Z-height cards."""
    try:
        hybrid = read(str(cif_path))
        total = len(hybrid)
        z_height = hybrid.cell[2, 2]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                '<div class="stat-card">'
                '<div class="stat-title">'
                "Total Atoms</div>"
                '<div class="stat-value">'
                f"{total}</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '<div class="stat-card">'
                '<div class="stat-title">'
                "Z Cell Height</div>"
                '<div class="stat-value">'
                f"{z_height:.2f} Å</div></div>",
                unsafe_allow_html=True,
            )
    except Exception:  # pylint: disable=broad-exception-caught
        st.write(
            "Could not parse atomic stats, "
            "showing raw message."
        )


def _download_buttons(
    cif, xyz, gen, prefix, sfx
):
    """Render download buttons for output files."""
    for path, label, ext in [
        (cif, "CIF", ".cif"),
        (xyz, "XYZ", ".xyz"),
        (gen, "GEN", ".gen"),
    ]:
        if path.exists():
            with open(
                path, "r", encoding="utf-8"
            ) as fh:
                st.download_button(
                    label=(
                        f"Download {label} structure "
                        f"({ext})"
                    ),
                    data=fh.read(),
                    file_name=f"{prefix}{sfx}{ext}",
                    mime="text/plain",
                    use_container_width=True,
                )


if __name__ == "__main__":
    main()
