$ErrorActionPreference = "Stop"
$filePath = "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG\CUs-RUs.xlsx"

Write-Output "Checking file exists..."
if (Test-Path $filePath) {
    Write-Output "File found: $filePath"
    Write-Output "File size: $((Get-Item $filePath).Length) bytes"
} else {
    Write-Output "ERROR: File not found at $filePath"
    exit 1
}

Write-Output "Creating Excel COM object..."
$xl = New-Object -ComObject Excel.Application
Write-Output "Excel COM object created successfully"
$xl.Visible = $false
$xl.DisplayAlerts = $false

try {
    Write-Output "Opening workbook..."
    $wb = $xl.Workbooks.Open($filePath)
    Write-Output "Workbook opened successfully"

    $ws = $wb.Sheets.Item(1)
    Write-Output "Sheet name: $($ws.Name)"

    # AUM from AD6
    $aum_raw = $ws.Range("AD6").Value2
    Write-Output "AUM_RAW=$aum_raw"

    # Revenue (Fwd 12 mth) from AE19
    $revenue = $ws.Range("AE19").Value2
    Write-Output "REVENUE=$revenue"

    # Units Outstanding - last non-empty value in column Q
    $lastRow = $ws.Cells($ws.Rows.Count, "Q").End(-4162).Row
    $units = $ws.Range("Q$lastRow").Value2
    Write-Output "UNITS=$units"
    Write-Output "UNITS_ROW=$lastRow"

    # Revenue concentration - U14:AA14 (7 cells)
    $values = @()
    $cols = @("U","V","W","X","Y","Z","AA")
    foreach ($col in $cols) {
        $cellRef = "${col}14"
        $val = $ws.Range($cellRef).Value2
        if ($null -ne $val -and $val -ne "") {
            $values += [double]$val
            Write-Output "CELL_${col}14=$val"
        } else {
            Write-Output "CELL_${col}14=EMPTY"
        }
    }

    # Sort descending
    $sorted = $values | Sort-Object -Descending
    $sep = ","
    $joinedValues = $sorted -join $sep
    Write-Output "SORTED_VALUES=$joinedValues"

    $maxVal = $sorted[0]
    $top3 = $sorted[0..2]
    $top3Sum = ($top3 | Measure-Object -Sum).Sum

    Write-Output "MAX_REVENUE=$maxVal"
    Write-Output "TOP3_SUM=$top3Sum"

    $pctTop = $maxVal / $revenue
    $pctTop3 = $top3Sum / $revenue
    Write-Output "PCT_TOP_ETF=$pctTop"
    Write-Output "PCT_TOP3_ETF=$pctTop3"

    $wb.Close($false)
    Write-Output "Workbook closed"
} catch {
    Write-Output "ERROR at line $($_.InvocationInfo.ScriptLineNumber): $($_.Exception.Message)"
} finally {
    $xl.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
    Write-Output "Excel COM released"
}
