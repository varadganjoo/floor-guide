$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$qaRoot = Join-Path $taskRoot 'qa'
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $taskRoot 'documents') -Filter '*.docx') {
        $document = $null
        try {
            $document = $word.Documents.Open($file.FullName, $false, $true)
            $document.Repaginate()
            $pdfPath = Join-Path $qaRoot ($file.BaseName + '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            Write-Output ($file.Name + ': ' + $document.ComputeStatistics(2) + ' pages')
        } finally {
            if ($null -ne $document) { $document.Close(0); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
        }
    }
} finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
