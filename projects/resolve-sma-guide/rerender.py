"""Post-process the planned.qmd to fix table column widths, then re-render."""

import shutil
import tempfile
from pathlib import Path
import sys

# Add resolve-docs to path
BRAND_ROOT = Path(__file__).resolve().parent.parent.parent / "references" / "brand-assets" / "resolve-am" / "latex-template"
sys.path.insert(0, str(BRAND_ROOT))

from resolve_docs.builder import render_with_quarto
from resolve_docs.service import prepare_workspace
from resolve_docs.profiles import get_profile

OUTPUT = Path(__file__).resolve().parent / "output"


def patch_planned_qmd(text: str) -> str:
    """Add col-widths to the onboarding table."""
    # Find the table-block div immediately before the "Step | Stage | What Happens" table
    old = '::: {.table-block}\n| Step | Stage | What Happens |'
    new = '::: {.table-block col-widths="0.4,0.8,1.8"}\n| Step | Stage | What Happens |'
    if old in text:
        text = text.replace(old, new)
        print("Patched onboarding table col-widths")
    else:
        print("WARNING: Could not find onboarding table to patch")
    return text


def main():
    profile = get_profile(brand="resolve", document_kind="report")
    planned_path = OUTPUT / "ReSolve SMA Guide.planned.qmd"
    tex_path = OUTPUT / "ReSolve SMA Guide.tex"
    pdf_path = OUTPUT / "ReSolve SMA Guide.pdf"

    # Patch the planned.qmd
    text = planned_path.read_text(encoding="utf-8")
    patched = patch_planned_qmd(text)
    planned_path.write_text(patched, encoding="utf-8")

    # Re-render using the pipeline's own workspace setup
    with tempfile.TemporaryDirectory(prefix="resolve-docs-render-") as render_tmp:
        render_workspace = Path(render_tmp).resolve()
        prepare_workspace(render_workspace, profile=profile)

        # Stage the input directory
        staged_dir = render_workspace / "input"
        staged_dir.mkdir(parents=True, exist_ok=True)
        staged_planned = staged_dir / planned_path.name
        shutil.copy2(planned_path, staged_planned)

        # Render LaTeX and PDF
        print("Rendering LaTeX...")
        render_with_quarto(staged_planned, profile.latex_format, tex_path, project_root=render_workspace)
        print("Rendering PDF...")
        render_with_quarto(staged_planned, profile.pdf_format, pdf_path, project_root=render_workspace)

    print(f"Done. PDF: {pdf_path}")


if __name__ == "__main__":
    main()
