$docxPath = (Resolve-Path "report\tieu_luan_toi_uu_csdl.docx").Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Total Pages: $($doc.ComputeStatistics(2))"
    Write-Host "Total Tables: $($doc.Tables.Count)"
    Write-Host "Total InlineShapes: $($doc.InlineShapes.Count)"
    
    if ($doc.TablesOfContents.Count -gt 0) {
        Write-Host "`n--- TOC PREVIEW ---"
        $tocLines = $doc.TablesOfContents.Item(1).Range.Text -split "`r`n|`n|`r"
        foreach ($line in $tocLines) {
            if ($line.Trim()) {
                Write-Host $line.Trim()
            }
        }
    }
    $doc.Close([ref]$false)
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}

