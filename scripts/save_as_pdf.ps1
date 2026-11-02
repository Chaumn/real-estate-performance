$docxPath = (Resolve-Path "report\tieu_luan_toi_uu_csdl.docx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($docxPath, ".pdf")

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $word.ActivePrinter = "Microsoft Print to PDF"
    Write-Host "Set ActivePrinter to Microsoft Print to PDF."
    
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Updating Fields and TOC..."
    foreach ($story in $doc.StoryRanges) {
        $story.Fields.Update()
    }
    foreach ($toc in $doc.TablesOfContents) {
        $toc.Update()
    }
    $pageCount = $doc.ComputeStatistics(2)
    Write-Host "Document Page Count: $pageCount"
    $doc.Save()
    Write-Host "Docx saved."

    Write-Host "Exporting to PDF/A via ExportAsFixedFormat (UseISO19005_1 = true)..."
    # wdExportFormatPDF = 17, wdExportOptimizeForPrint = 0, wdExportCreateHeadingBookmarks = 1, UseISO19005_1 = true
    $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $false, $true)
    Write-Host "Export finished."

    if (Test-Path $pdfPath) {
        $pdfSize = (Get-Item $pdfPath).Length
        Write-Host "PDF File Created Successfully: $pdfSize bytes ($pdfPath)"
    } else {
        Write-Host "PDF file not found."
    }

    $doc.Close([ref]$false)
}
catch {
    Write-Error "Error: $_"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
