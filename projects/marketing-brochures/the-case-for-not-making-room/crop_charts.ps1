Add-Type -AssemblyName System.Drawing

$baseDir = 'C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\Project_Repository_RAM_RS\The_Case_for_Not_Making_Room_for_alts\chart_exports'

function Crop-And-Trim {
    param($inputPath, $outputPath, $x, $y, $width, $height)

    $src = [System.Drawing.Image]::FromFile($inputPath)
    $bmp = New-Object System.Drawing.Bitmap($width, $height)
    $bmp.SetResolution($src.HorizontalResolution, $src.VerticalResolution)

    $cropRect = New-Object System.Drawing.Rectangle($x, $y, $width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.Clear([System.Drawing.Color]::FromArgb(242, 242, 242))
    $graphics.DrawImage($src, 0, 0, $cropRect, [System.Drawing.GraphicsUnit]::Pixel)
    $graphics.Dispose()
    $src.Dispose()

    Write-Host "  Crop: ${width}x${height} from ($x,$y)"

    # Auto-trim: anything with ALL channels in 237..247 is slide background
    $pad = 25
    $minX = $width; $maxX = 0; $minY = $height; $maxY = 0

    for ($py = 0; $py -lt $height; $py += 2) {
        for ($px = 0; $px -lt $width; $px += 2) {
            $p = $bmp.GetPixel($px, $py)
            if ($p.R -lt 237 -or $p.R -gt 247 -or $p.G -lt 237 -or $p.G -gt 247 -or $p.B -lt 237 -or $p.B -gt 247) {
                if ($px -lt $minX) { $minX = $px }
                if ($px -gt $maxX) { $maxX = $px }
                if ($py -lt $minY) { $minY = $py }
                if ($py -gt $maxY) { $maxY = $py }
            }
        }
    }

    Write-Host "  Content bounds: ($minX,$minY) to ($maxX,$maxY)"

    if ($maxX -le $minX -or $maxY -le $minY) {
        Write-Host "  WARNING: No content found, saving full crop"
        $bmp.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $bmp.Dispose()
        return
    }

    $trimX = [Math]::Max(0, $minX - $pad)
    $trimY = [Math]::Max(0, $minY - $pad)
    $trimW = [Math]::Min($width - $trimX, ($maxX - $minX) + 2 * $pad)
    $trimH = [Math]::Min($height - $trimY, ($maxY - $minY) + 2 * $pad)

    Write-Host "  Trimming to: x=$trimX y=$trimY w=$trimW h=$trimH"

    $trimRect = New-Object System.Drawing.Rectangle($trimX, $trimY, $trimW, $trimH)
    $trimBmp = New-Object System.Drawing.Bitmap($trimW, $trimH)
    $trimBmp.SetResolution($bmp.HorizontalResolution, $bmp.VerticalResolution)
    $tg = [System.Drawing.Graphics]::FromImage($trimBmp)
    $tg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $tg.Clear([System.Drawing.Color]::FromArgb(242, 242, 242))
    $tg.DrawImage($bmp, 0, 0, $trimRect, [System.Drawing.GraphicsUnit]::Pixel)
    $tg.Dispose()
    $bmp.Dispose()

    $trimBmp.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $trimBmp.Dispose()

    $size = (Get-Item $outputPath).Length
    Write-Host "  Saved: $outputPath ($size bytes, ${trimW}x${trimH})"
}

# ── Slide 2: Growth-of-$1 line chart ──────────────────────────────────
# Previous crop at y=845 showed body text "portfolios..." at top.
# Push down to y=885 to clear body text. Chart "$800" label is ~y=895.
# Height reduced to 850 (reaches y=1735, includes source text at y≈1720).
Write-Host "Cropping chart_growth..."
Crop-And-Trim "$baseDir\slide2.png" "$baseDir\chart_growth.png" 160 885 3360 850

# ── Slide 3: Two donut pie charts ──────────────────────────────────────
# Previous crop at y=930 showed bullet text + bold "Good diversification..."
# Bold text wraps two lines ending ~y=1010. Pie circles start ~y=1000.
# Push to y=1005 — clips top few pixels of bold text while keeping pie tops.
# Height 830 reaches y=1835 (includes footnote at y≈1770).
Write-Host "`nCropping chart_pies..."
Crop-And-Trim "$baseDir\slide3.png" "$baseDir\chart_pies.png" 80 1005 3300 830

# ── Slide 5: Stacked bar diagram ──────────────────────────────────────
# Previous crop at y=305 showed "sification" from main slide title.
# Main title "...Diversification" ends ~y=360. Push to y=375.
# Chart title "Example Structure..." starts at y≈385.
# Height 1380 reaches y=1755 (includes source text at y≈1720).
Write-Host "`nCropping chart_stackedbar..."
Crop-And-Trim "$baseDir\slide5.png" "$baseDir\chart_stackedbar.png" 2020 375 1520 1380

Write-Host "`nAll crops done."
