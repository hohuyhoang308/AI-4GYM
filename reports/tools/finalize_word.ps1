param([string[]]$Paths)
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
try {
    foreach ($item in $Paths) {
        $resolvedDocumentPath = (Resolve-Path -LiteralPath $item).Path
        $document = $word.Documents.Open($resolvedDocumentPath, $false, $false)
        try {
            $null = $document.Fields.Update()
            foreach ($toc in $document.TablesOfContents) { $toc.Update() }
            $document.Repaginate()
            foreach ($toc in $document.TablesOfContents) { $toc.UpdatePageNumbers() }
            $document.Save()
            $pdfPath = [System.IO.Path]::ChangeExtension($resolvedDocumentPath, '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            Write-Output ([PSCustomObject]@{Path=$resolvedDocumentPath; Pages=$document.ComputeStatistics(2); PDF=$pdfPath} | ConvertTo-Json -Compress)
        } finally {
            $document.Close(0)
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)
        }
    }
} finally {
    $word.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
