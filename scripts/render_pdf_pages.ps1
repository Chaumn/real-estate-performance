param(
    [string]$pdfPath = "report\tieu_luan_toi_uu_csdl.pdf",
    [string]$outDir = "report\rendered_pages",
    [int[]]$pages = @(1, 2, 3, 5, 12, 20, 35, 45, 55)
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime

$pdfFullPath = (Resolve-Path $pdfPath).Path
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

[Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFolder, Windows.Storage, ContentType = WindowsRuntime] | Out-Null

function Await($asyncOp, [Type]$resultType) {
    if ($resultType) {
        $asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
            $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 
        }
        $task = $asTaskGeneric[0].MakeGenericMethod($resultType).Invoke($null, @($asyncOp))
        return $task.Result
    } else {
        $asTaskAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
            $_.Name -eq 'AsTask' -and -not $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
        }
        $task = $asTaskAction[0].Invoke($null, @($asyncOp))
        $task.Wait()
    }
}

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfFullPath)) ([Windows.Storage.StorageFile])
$pdfDoc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])

Write-Host "PDF Document Loaded: $($pdfDoc.PageCount) pages total."

$folder = Await ([Windows.Storage.StorageFolder]::GetFolderFromPathAsync((Resolve-Path $outDir).Path)) ([Windows.Storage.StorageFolder])

foreach ($pNum in $pages) {
    if ($pNum -le $pdfDoc.PageCount) {
        $page = $pdfDoc.GetPage($pNum - 1)
        $fileName = ("page_{0:D2}.png" -f $pNum)
        $outImgPath = Join-Path $outDir $fileName
        
        $imgFile = Await ($folder.CreateFileAsync($fileName, [Windows.Storage.CreationCollisionOption]::ReplaceExisting)) ([Windows.Storage.StorageFile])
        $stream = Await ($imgFile.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)) ([Windows.Storage.Streams.IRandomAccessStream])
        
        $renderOpt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
        $renderOpt.DestinationWidth = [uint32]2000
        Await ($page.RenderToStreamAsync($stream, $renderOpt)) $null
        
        $flushOp = $stream.FlushAsync()
        Await $flushOp ([bool]) | Out-Null
        $stream.Dispose()
        Write-Host "Rendered Page $pNum -> $outImgPath"
    }
}
Write-Host "Rendering completed successfully."
