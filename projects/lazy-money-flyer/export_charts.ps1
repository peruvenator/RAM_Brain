# Export slides 4, 5, 7, and 8 from the Lazy Money PPTX at high resolution
# Uses PowerPoint COM automation (requires PowerPoint installed)

$ErrorActionPreference = "Stop"

$pptxPath = Resolve-Path "$PSScriptRoot\..\..\..\..\Downloads RG\RAM Lazy money flyer content.pptx" -ErrorAction Stop
$outDir = "$PSScriptRoot\chart_exports"

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

Write-Host "Opening PowerPoint..."
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue

try {
    $pres = $ppt.Presentations.Open($pptxPath.Path, [Microsoft.Office.Core.MsoTriState]::msoTrue)

    # Export target slides at 4000x2250 (roughly 300 DPI for widescreen)
    $slidesToExport = @(4, 5, 7, 8)
    $width = 4000
    $height = 2250

    foreach ($slideNum in $slidesToExport) {
        $outFile = Join-Path $outDir "slide${slideNum}.png"
        Write-Host "Exporting slide $slideNum -> $outFile"
        $slide = $pres.Slides.Item($slideNum)
        $slide.Export($outFile, "PNG", $width, $height)
    }

    Write-Host "Done. Exported slides: $($slidesToExport -join ', ')"
}
finally {
    if ($pres) { $pres.Close() }
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
}
