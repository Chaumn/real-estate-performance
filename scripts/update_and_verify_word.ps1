$docxPath = (Resolve-Path "report\tieu_luan_toi_uu_csdl.docx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($docxPath, ".pdf")

Write-Host "Starting Word Application COM automation..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Document opened successfully."

    Write-Host "Updating all Fields..."
    foreach ($story in $doc.StoryRanges) {
        $story.Fields.Update()
    }

    Write-Host "Updating Tables of Contents..."
    foreach ($toc in $doc.TablesOfContents) {
        $toc.Update()
    }

    $pageCount = $doc.ComputeStatistics(2) # wdStatisticPages
    $wordCount = $doc.ComputeStatistics(0) # wdStatisticWords
    $tableCount = $doc.Tables.Count
    $shapeCount = $doc.InlineShapes.Count

    Write-Host "=== Document Statistics ==="
    Write-Host "- Total Pages: $pageCount"
    Write-Host "- Total Words: $wordCount"
    Write-Host "- Total Tables: $tableCount"
    Write-Host "- Total Inline Shapes (Charts): $shapeCount"

    $doc.Save()
    Write-Host "Saved updated docx."

    Write-Host "Exporting to PDF: $pdfPath..."
    # 17 = wdExportFormatPDF, 0 = wdExportOptimizeForPrint, 1 = wdExportCreateHeadingBookmarks
    $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1)
    
    $pdfSize = (Get-Item $pdfPath).Length
    Write-Host "PDF exported successfully: $pdfSize bytes."

    $doc.Close($false)
    Write-Host "Validation completed successfully."
}
catch {
    Write-Error "Error: $_"
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

