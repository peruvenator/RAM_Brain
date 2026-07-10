# Office-to-SVG Extraction - Skill Reference

## Overview

Bulk-extract charts, shapes, and images from Microsoft Office files (PowerPoint, Excel) as true SVG vector files using PowerShell COM automation.

Two scripts handle the two main Office applications:
- **`export_shapes_svg.ps1`** - PowerPoint (.pptx)
- **`export_excel_svg.ps1`** - Excel (.xlsx)

---

## Quick Usage

### PowerPoint -> SVG

```powershell
# Export all shapes from a PPTX as SVG
.\export_shapes_svg.ps1 -PptxPath "MyPresentation.pptx" -OutputDir ".\svg_output"

# Keep intermediate EMF files for debugging
.\export_shapes_svg.ps1 -PptxPath "MyPresentation.pptx" -KeepEMF
```

### Excel -> SVG

```powershell
# Export all charts from an XLSX as SVG
.\export_excel_svg.ps1 -XlsxPath "MyWorkbook.xlsx" -OutputDir ".\svg_output"

# Keep intermediate EMF files for debugging
.\export_excel_svg.ps1 -XlsxPath "MyWorkbook.xlsx" -KeepEMF
```

---

## Requirements

| Requirement | Purpose | Install |
|-------------|---------|---------|
| **Microsoft Office** (365 / 2021+) | COM automation for PowerPoint and Excel | - |
| **Inkscape** | EMF -> SVG conversion (PowerPoint pipeline, Excel fallback) | `winget install Inkscape.Inkscape` |

> **Note**: Inkscape is required for PowerPoint exports (all shapes go through EMF -> SVG). For Excel charts, Inkscape is only needed as a fallback - the primary path extracts SVG directly from the clipboard.

---

## How Each Pipeline Works

### PowerPoint Pipeline (EMF -> Inkscape -> SVG)

PowerPoint doesn't support direct SVG export via COM. The pipeline:

1. **Open** the PPTX via `New-Object -ComObject PowerPoint.Application`
2. **For each shape** on each slide:
   - `$shape.Export($emfPath, 5)` - exports as EMF (format code 5 = `ppShapeFormatEMF`)
3. **Convert** each EMF -> SVG via Inkscape CLI:
   - `inkscape "input.emf" --export-filename="output.svg"`
4. **Clean up** intermediate EMF files (unless `-KeepEMF`)

**Key detail**: The PowerPoint `Shape.Export()` format codes are:
| Code | Format |
|------|--------|
| 0 | GIF |
| 1 | JPG |
| 2 | PNG |
| 3 | BMP |
| 4 | WMF |
| 5 | EMF (vector - use this!) |
| 6+ | Invalid (silently falls back to JPEG!) |

### Excel Pipeline (Clipboard SVG - Direct!)

Excel 365 puts `image/svg+xml` on the Windows clipboard when copying chart areas:

1. **Open** the XLSX via `New-Object -ComObject Excel.Application`
2. **For each chart** on each sheet:
   - `$chartObj.Activate()` - **critical!** Chart must be active first
   - `$chart.ChartArea.Copy()` - copies chart to clipboard with multiple formats
   - Extract `image/svg+xml` from clipboard via native Win32 API (`RegisterClipboardFormat`, `GetClipboardData`)
   - Save the UTF-8 SVG string directly to `.svg` file
3. **Fallback** (if SVG not on clipboard):
   - `$chartObj.CopyPicture(1, -4147)` - copies as EMF to clipboard (xlScreen=1, xlPicture=-4147)
   - Save EMF from clipboard via `GetEnhMetaFileBits` Win32 API
   - Convert EMF -> SVG via Inkscape CLI
4. **Non-chart shapes**: Same EMF clipboard -> Inkscape pipeline as fallback

---

## Critical Gotchas & Lessons Learned

### Excel - Chart.Export() Produces 0-Byte Files

`$chart.Export($path, "PNG")` returns `True` but creates 0-byte files **unless the chart is activated first** via `$chartObj.Activate()`. Even with activation, EMF export still produces 0-byte files. The clipboard approach (`ChartArea.Copy()`) is far more reliable.

### Excel - CopyPicture Format Constants

The second argument to `CopyPicture()` is the **format**, NOT the appearance:
- `xlPicture = -4147` -> Enhanced Metafile (EMF) - **use this for vector**
- `xlBitmap = 2` -> Bitmap (raster)

Using `2` gives bitmap, NOT metafile. This is easy to confuse since `xlPrinter = 2` for the first (appearance) argument.

### Excel - Clipboard SVG Requires Retry

Excel's clipboard operations are asynchronous. Sometimes `ChartArea.Copy()` completes before all clipboard formats are ready. The export script uses up to 3 retry attempts with 500ms delays between them.

### Excel - ClipboardHelper Requires Native Win32

`System.Windows.Forms.Clipboard.GetDataObject()` doesn't expose custom clipboard formats like `image/svg+xml`. A C# helper class using `RegisterClipboardFormat()`, `OpenClipboard()`, `GetClipboardData()`, `GlobalLock()`, and `GlobalSize()` is compiled inline via `Add-Type` to read the SVG data.

### PowerPoint - Format Code 8 Does NOT Mean SVG

`Shape.Export($path, 8)` silently falls back to JPEG output. The PpShapeFormat enum only goes up to 5 (EMF). Any code > 5 produces JPEG with the wrong file extension.

### PowerPoint - Slide.Export("SVG") Not Supported

On Office build 16.0/19725, `Slide.Export($path, "SVG")` throws "no installed converter supports this file type." This may work on newer Office builds.

### Inkscape - Startup Overhead

Each Inkscape CLI invocation takes ~2-3 seconds (JVM-like startup cost). For 66 shapes from a PPTX, expect ~3-4 minutes total conversion time. There's no batch mode for EMF -> SVG in Inkscape.

### Add-Type - Same Session Conflict

If a PowerShell session already has a type loaded (e.g., `ClipboardSvgHelper`), re-running `Add-Type` with the same class name will fail. The Excel script wraps `Add-Type` in a try/catch that checks if the type already exists.

---

## Output File Naming

### PowerPoint
```
svg_exports/
  slide1_Title_1.svg            # Slide 1, shape "Title 1"
  slide1_Chart_3.svg            # Slide 1, shape "Chart 3"
  slide2_Picture_5.svg          # Slide 2, shape "Picture 5"
  ...
```

### Excel
```
excel_svg_exports/
  Sheet1_Chart_1.svg            # Sheet "Sheet1", chart "Chart 1"
  Sheet1_Chart_2.svg
  Sheet1_Picture_3.emf -> .svg  # Non-chart shape via Inkscape
  Revenue_Chart_1.svg           # Sheet "Revenue", chart "Chart 1"
  ...
```

---

## Adapting for New Files

### Changing the Default Input File

Both scripts use `$PSScriptRoot` (the script's own directory) to find the default input file. Edit the `param()` block at the top:

```powershell
# PowerPoint
param(
    [string]$PptxPath = "$PSScriptRoot\YourFile.pptx",
    ...
)

# Excel
param(
    [string]$XlsxPath = "$PSScriptRoot\YourFile.xlsx",
    ...
)
```

Or pass the path on the command line - no script edits needed:

```powershell
.\export_shapes_svg.ps1 -PptxPath "C:\path\to\any.pptx"
.\export_excel_svg.ps1 -XlsxPath "C:\path\to\any.xlsx"
```

### Adding Support for New Office Apps

The same patterns can be extended to Word:
- Word COM: `New-Object -ComObject Word.Application`
- Shapes: `$doc.InlineShapes` and `$doc.Shapes`
- Charts in Word: `$shape.Chart.ChartArea.Copy()` (same clipboard SVG trick may work)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Inkscape not found" | `winget install Inkscape.Inkscape` then restart terminal |
| 0-byte EMF files (Excel) | Use clipboard approach, not `Chart.Export()` |
| JPEG files with .svg extension | Format code was wrong; use code 5 for EMF in PowerPoint |
| "Cannot add type" compilation error | Type already loaded in session; restart PowerShell or use try/catch guard |
| Clipboard formats missing SVG | Increase `Start-Sleep` delays; retry up to 3 times |
| Charts fail intermittently | Add `$sheet.Activate()` before `$chartObj.Activate()` |
| "Specified cast is not valid" | COM interop issue; avoid `Shapes.Paste()` in PowerPoint, use `Shape.Export()` directly |

---

## Files in This Project

| File | Purpose |
|------|---------|
| `export_shapes_svg.ps1` | **PowerPoint -> SVG** extraction script |
| `export_excel_svg.ps1` | **Excel -> SVG** extraction script |
| `OFFICE_SVG_EXTRACTION.md` | This skill reference document |
| `svg_exports/` | Output directory for PowerPoint SVGs |
| `excel_svg_exports/` | Output directory for Excel SVGs |
| `test_excel_export.ps1` | Diagnostic: tested Excel Chart.Export filter strings |
| `test_excel_export2.ps1` | Diagnostic: tested activation + clipboard approaches |
| `test_excel_export3.ps1` | Diagnostic: proved SVG clipboard extraction works |
| `test_svg_export.ps1` | Diagnostic: tested PowerPoint export format codes |
