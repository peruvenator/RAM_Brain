$pptxPath = 'C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\Project_Repository_RAM_RS\The_Case_for_Not_Making_Room_for_alts\The_Case_for_NOT_Making_Room_for_Alternatives.pptx'
$outputDir = 'C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\Project_Repository_RAM_RS\The_Case_for_Not_Making_Room_for_alts\chart_exports'

# Create output directory
if (-not (Test-Path $outputDir)) { New-Item -ItemType Directory -Path $outputDir | Out-Null }

# MsoTriState enum values
$msoTrue = -1
$msoFalse = 0

# Open PowerPoint
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $msoTrue

# Open presentation: (path, ReadOnly, HasTitle, Window)
$presentation = $ppt.Presentations.Open($pptxPath, $msoTrue, $msoFalse, $msoFalse)

Write-Host "Presentation opened. Total slides: $($presentation.Slides.Count)"

# Export slides 2, 3, 5 at high resolution (4000px wide ~ 300 DPI)
$slidesToExport = @(2, 3, 5)

foreach ($slideNum in $slidesToExport) {
    $slide = $presentation.Slides.Item($slideNum)
    $exportPath = Join-Path $outputDir "slide$slideNum.png"
    $slide.Export($exportPath, "PNG", 4000, 2250)

    if (Test-Path $exportPath) {
        $size = (Get-Item $exportPath).Length
        Write-Host "Exported slide $slideNum -> $exportPath ($size bytes)"
    } else {
        Write-Host "FAILED to export slide $slideNum"
    }
}

# Close and cleanup
$presentation.Close()
$ppt.Quit()

[System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
[System.GC]::Collect()

Write-Host "Done."
