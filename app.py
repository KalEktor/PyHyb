# -*- coding: utf-8 -*-
"""
PyHyB Streamlit Web Interface
-----------------------------
A visually stunning, interactive web application to construct hybrid configurations
by combining molecular structures (.xyz) with periodic substrates (.cif) in 3D.
"""

import tempfile
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from ase.io import read

# Import PyHyB workflow components
from pyhyb.core.hybrid_runner import HybridWorkflowRunner

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent


def render_3d_molecule(struct_text: str, file_format: str = "xyz", height: int = 400):
    """
    Renders the structure using py3Dmol.js directly via HTML iframe.
    No heavy python packages required.
    """
    # Clean the molecule text string to safe Javascript string
    safe_text = struct_text.replace("`", "\\`").replace("\n", "\\n").replace("\r", "")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                background-color: #0f172a;
            }}
            #container-3d {{
                width: 100%;
                height: 100%;
                position: relative;
            }}
            .viewer-label {{
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(15, 23, 42, 0.85);
                color: #f8fafc;
                padding: 4px 10px;
                border-radius: 6px;
                font-family: sans-serif;
                font-size: 12px;
                z-index: 10;
                pointer-events: none;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        </style>
        <script src="https://3dmol.org/build/3Dmol-min.js"></script>
    </head>
    <body>
        <div class="viewer-label">
            {file_format.upper()} Viewer (Drag to rotate, Scroll to zoom)
        </div>
        <div id="container-3d"></div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                let element = document.getElementById("container-3d");
                let viewer = $3Dmol.createViewer(element, {{ backgroundColor: '#0f172a' }});
                let data = `{safe_text}`;

                viewer.addModel(data, "{file_format}");

                // Styling
                viewer.setStyle({{}}, {{
                    sphere: {{ scale: 0.28, colorscheme: 'Jmol' }},
                    stick: {{ radius: 0.08, colorscheme: 'Jmol' }}
                }});

                // Add unit cell box if it's a CIF file
                if ("{file_format}" === "cif") {{
                    viewer.addUnitCell();
                }}

                viewer.zoomTo();
                viewer.render();
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_content, height=height)


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def main():
    """Main function containing all Streamlit page logic."""
    # Set up page configurations
    st.set_page_config(
        page_title="PyHyB: Hybrid Material Builder",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Premium Font and Custom Styling
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            /* Custom typography and fonts */
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
            }

            /* Glassmorphic card styling compatible with light/dark modes */
            .stat-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.15);
                margin-bottom: 1rem;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .stat-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 12px 25px -4px rgba(0, 0, 0, 0.25);
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
                font-size: 2rem;
                font-weight: 800;
                background: linear-gradient(135deg, #60a5fa 0%, #34d399 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-family: 'Outfit', sans-serif;
            }

            /* Sidebar styling overrides */
            [data-testid="stSidebar"] {
                background-color: #0f172a;
                color: #f8fafc;
                border-right: 1px solid #1e293b;
            }
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
                color: #94a3b8;
            }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
                color: #ffffff !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Page Title Banner (Clean Text-Only Brand)
    st.markdown("""
        <div style="background-color: #0f172a; padding: 2rem; border-radius: 18px; margin-bottom: 2rem; border: 1px solid #1e293b; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4); text-align: center;">
            <h1 style="margin: 0; font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa 0%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-family: 'Outfit', sans-serif; letter-spacing: -1.5px;">
                PyHyB
            </h1>
            <p style="margin: 0.5rem 0 0 0; font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #94a3b8; font-weight: 400; letter-spacing: 1.5px; text-transform: uppercase;">
                Molecular Hybrid Technology
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar setup for configurations
    with st.sidebar:
        st.markdown("## ⚙️ Build Options")
        st.markdown(
            "Configure how your macromolecule will be positioned and checked on "
            "the substrate."
        )

        placement = st.selectbox(
            "Placement Logic",
            options=["center", "surface"],
            index=0,
            help=(
                "center: Center molecule in middle of the unit cell Z space.\n"
                "surface: Place bottom of molecule target distance above the "
                "highest substrate atom."
            )
        )

        distance = st.slider(
            "Starting Height (Å)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            help="Only applied for 'surface' placement logic."
        )

        collision_threshold = st.slider(
            "Collision Threshold (Å)",
            min_value=0.5,
            max_value=4.0,
            value=1.5,
            step=0.1,
            help=(
                "Minimum allowed distance between macromolecule and substrate "
                "atoms. Molecule is shifted up if below this."
            )
        )

        st.markdown("### 🔄 Molecule Rotation")
        st.markdown(
            "Pre-rotate the macromolecule around its Center of Mass (COM) "
            "before depositing."
        )
        rot_x = st.slider("Rotate X (°)", 0.0, 360.0, 0.0, step=5.0)
        rot_y = st.slider("Rotate Y (°)", 0.0, 360.0, 0.0, step=5.0)
        rot_z = st.slider("Rotate Z (°)", 0.0, 360.0, 0.0, step=5.0)

        rotation_args = (
            [rot_x, rot_y, rot_z]
            if (rot_x != 0 or rot_y != 0 or rot_z != 0)
            else None
        )

        st.markdown("### 📁 Output File Naming")
        prefix_val = st.text_input(
            "Custom File Prefix",
            value="hybrid_structure",
            help=(
                "Choose a custom prefix name for your combined outputs "
                "(e.g. 'graphene_glycine')."
            )
        ).strip()
        prefix_arg = prefix_val if prefix_val else None

        # Hardcoded defaults for relaxation (since DFTB+ is disabled in the GUI)
        optimize = False
        fmax = 0.05
        steps = 200

    # File upload columns
    col_inputs, col_visualizers = st.columns([1, 1])

    with col_inputs:
        st.subheader("📤 1. Upload Structures")

        # Left: Molecule uploader
        uploaded_material = st.file_uploader(
            "Upload Macromolecule (.xyz)",
            type=["xyz"],
            help="Select a standard molecular .xyz structure file."
        )

        # Right: Substrate uploader
        uploaded_substrate = st.file_uploader(
            "Upload Periodic Substrate (.cif)",
            type=["cif"],
            help="Select a periodic substrate .cif crystal structure file."
        )

        st.markdown("---")
        st.subheader("💡 Load Verification Examples")
        st.write("Test PyHyB immediately using provided benchmark structures:")

        col_ex1, col_ex2, col_ex3 = st.columns(3)

        # Example paths resolution
        glycine_xyz_path = PROJECT_ROOT / "example" / "data" / "glycine.xyz"
        graphene_cif_path = PROJECT_ROOT / "example" / "data" / "graphene_7x7.cif"
        crown_xyz_path = PROJECT_ROOT / "example" / "data" / "crown_ether.xyz"
        cucurbit_xyz_path = PROJECT_ROOT / "example" / "data" / "cucurbituril.xyz"
        graphene_oxide_cif_path = (
            PROJECT_ROOT / "example" / "data" / "graphene_oxide.cif"
        )

        # Session state checks to handle examples loading
        if "material_content" not in st.session_state:
            st.session_state.material_content = None
            st.session_state.material_name = None
        if "substrate_content" not in st.session_state:
            st.session_state.substrate_content = None
            st.session_state.substrate_name = None

        if col_ex1.button("🧬 Load Glycine on Graphene"):
            with open(glycine_xyz_path, "r", encoding="utf-8") as f:
                st.session_state.material_content = f.read()
                st.session_state.material_name = "glycine.xyz"
            with open(graphene_cif_path, "r", encoding="utf-8") as f:
                st.session_state.substrate_content = f.read()
                st.session_state.substrate_name = "graphene_7x7.cif"
            st.success("Glycine & Graphene examples loaded! Click 'Construct' below.")

        if col_ex2.button("🍩 Load Crown Ether"):
            with open(crown_xyz_path, "r", encoding="utf-8") as f:
                st.session_state.material_content = f.read()
                st.session_state.material_name = "crown_ether.xyz"
            with open(graphene_cif_path, "r", encoding="utf-8") as f:
                st.session_state.substrate_content = f.read()
                st.session_state.substrate_name = "graphene_7x7.cif"
            st.success("Crown Ether loaded! Click 'Construct' below.")

        if col_ex3.button("🛡️ Load Cucurbituril"):
            with open(cucurbit_xyz_path, "r", encoding="utf-8") as f:
                st.session_state.material_content = f.read()
                st.session_state.material_name = "cucurbituril.xyz"
            with open(graphene_oxide_cif_path, "r", encoding="utf-8") as f:
                st.session_state.substrate_content = f.read()
                st.session_state.substrate_name = "graphene_oxide.cif"
            st.success("Cucurbituril & Graphene Oxide loaded! Click 'Construct' below.")

        # Override session state values if manual file uploads occur
        if uploaded_material:
            st.session_state.material_content = (
                uploaded_material.getvalue().decode("utf-8")
            )
            st.session_state.material_name = uploaded_material.name
        if uploaded_substrate:
            st.session_state.substrate_content = (
                uploaded_substrate.getvalue().decode("utf-8")
            )
            st.session_state.substrate_name = uploaded_substrate.name

    # 3D Visualizer details for uploaded structures
    with col_visualizers:
        st.subheader("👁️ 2. Structure Previews")

        if st.session_state.material_content or st.session_state.substrate_content:
            tab_mat, tab_sub = st.tabs(["Macromolecule", "Substrate"])

            with tab_mat:
                if st.session_state.material_content:
                    st.markdown(f"**Filename:** `{st.session_state.material_name}`")
                    render_3d_molecule(st.session_state.material_content, file_format="xyz")
                else:
                    st.info("No macromolecule file uploaded or loaded yet.")

            with tab_sub:
                if st.session_state.substrate_content:
                    st.markdown(f"**Filename:** `{st.session_state.substrate_name}`")
                    render_3d_molecule(
                        st.session_state.substrate_content,
                        file_format="cif"
                    )
                else:
                    st.info("No periodic substrate file uploaded or loaded yet.")
        else:
            st.info(
                "Upload files or load a verification example to preview input "
                "structures in 3D."
            )

    # ----------------- EXECUTION AND OUTPUTS -----------------
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.subheader("🚀 3. Construct Hybrid Material")

    if not st.session_state.material_content or not st.session_state.substrate_content:
        st.warning(
            "Please upload both a macromolecule (.xyz) and substrate (.cif) "
            "structure above to continue."
        )
    else:
        # Action build button
        if st.button("Construct Hybrid Structure 🔨", type="primary", use_container_width=True):
            with st.spinner("Executing PyHyB structure building and checks..."):
                # Create a temporary directory to host inputs and execute build
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir)

                    # Write current files into the temp directory
                    mat_file = tmp_path / "molecule.xyz"
                    sub_file = tmp_path / "substrate.cif"
                    out_dir = tmp_path / "output"
                    out_dir.mkdir(exist_ok=True)

                    with open(mat_file, "w", encoding="utf-8") as f:
                        f.write(st.session_state.material_content)
                    with open(sub_file, "w", encoding="utf-8") as f:
                        f.write(st.session_state.substrate_content)

                    # Run the PyHyB workflow runner safely
                    runner = HybridWorkflowRunner()

                    success, result_message = runner.run(
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
                        steps=steps
                    )

                    if success:
                        st.success("Hybrid structure constructed successfully!")

                        # Resolve suffix depending on optimization selection
                        out_prefix = prefix_val if prefix_val else "hybrid_structure"
                        suffix = "_opt" if optimize else ""
                        cif_out = out_dir / f"{out_prefix}{suffix}.cif"
                        xyz_out = out_dir / f"{out_prefix}{suffix}.xyz"
                        gen_out = out_dir / f"{out_prefix}{suffix}.gen"

                        # Display summary and details
                        col_det, col_vis = st.columns([1, 1])

                        with col_det:
                            st.subheader("📋 Build Details")

                            # Generate some nice cards
                            try:
                                # Read final structure with ASE to extract stats
                                hybrid_atoms = read(str(cif_out))
                                total_atoms = len(hybrid_atoms)
                                c_param = hybrid_atoms.cell[2, 2]

                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"""
                                        <div class="stat-card">
                                            <div class="stat-title">Total Atoms</div>
                                            <div class="stat-value">{total_atoms}</div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                with c2:
                                    st.markdown(f"""
                                        <div class="stat-card">
                                            <div class="stat-title">Z Cell Height</div>
                                            <div class="stat-value">{c_param:.2f} Å</div>
                                        </div>
                                    """, unsafe_allow_html=True)
                            except Exception:  # pylint: disable=broad-exception-caught
                                st.write("Could not parse atomic stats, showing raw message.")

                            # Download buttons
                            st.subheader("💾 Download Output Files")

                            if cif_out.exists():
                                with open(cif_out, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        label="Download CIF structure (.cif)",
                                        data=f.read(),
                                        file_name=f"{out_prefix}{suffix}.cif",
                                        mime="text/plain",
                                        use_container_width=True
                                    )

                            if xyz_out.exists():
                                with open(xyz_out, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        label="Download XYZ structure (.xyz)",
                                        data=f.read(),
                                        file_name=f"{out_prefix}{suffix}.xyz",
                                        mime="text/plain",
                                        use_container_width=True
                                    )

                            if gen_out.exists():
                                with open(gen_out, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        label="Download GEN structure (.gen)",
                                        data=f.read(),
                                        file_name=f"{out_prefix}{suffix}.gen",
                                        mime="text/plain",
                                        use_container_width=True
                                    )

                            with st.expander("📝 View Execution Log details"):
                                st.code(result_message)
                                log_path = out_dir / "build.log"
                                if log_path.exists():
                                    with open(log_path, "r", encoding="utf-8") as lf:
                                        st.text(lf.read())

                        with col_vis:
                            st.subheader("🔬 3D Hybrid Structure Inspection")
                            if cif_out.exists():
                                with open(cif_out, "r", encoding="utf-8") as f:
                                    render_3d_molecule(f.read(), file_format="cif", height=450)
                    else:
                        st.error(f"Failed to combine structures:\n{result_message}")


if __name__ == "__main__":
    main()
