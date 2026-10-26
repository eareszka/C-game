param([switch]$Generate)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$previousAssumeYes = $env:PIXELLAB_ASSUME_YES
Push-Location $root
try {
    $env:PIXELLAB_ASSUME_YES = '0'
    $folder = 'art/enemies/pixellab/61_roperite/running'
    $action = 'Looping sprint in place, facing the same direction throughout. Alternate two long bird legs through contact, push-off, flight and recovery, with small body bob and a trailing orange segmented rattle tail. Rope snout lasso bounces as one clear loop with one forward flick at the middle of the cycle, then recoils into its original loop. Preserve creature anatomy, scale, tiny pixel clusters, one-pixel black outlines and flat colors; no camera motion or translation. No extra limbs, no trails or effects. Seamless loop.'
    foreach ($direction in @('D','DR','R','UR','U')) {
        if ($Generate -and (Test-Path "$folder/$direction-result.json")) {
            Write-Output "$direction already collected; reusing its saved result"
            continue
        }
        $inputFile = "$folder/inputs/$direction.png"
        if (!(Test-Path -LiteralPath $inputFile)) { throw "Missing $inputFile" }
        $common = @('--json', '--workspace', 'pixellab-out/61-roperite-animation', '--subject', "61-roperite-run-$direction")
        $request = @('animate', $inputFile, '--action', $action, '--frames', '8', '--transparent', '--name', "roperite-run-$direction")
        $dry = & pixellab-cli @common --dry-run @request
        if ($LASTEXITCODE) { throw "Dry run failed: $direction" }
        $dry | Set-Content "$folder/$direction-dry-run.json" -Encoding UTF8
        $data = ($dry -join "`n") | ConvertFrom-Json
        if (!$data.dry_run -or $data.estimated_cost.generations -gt 1) { throw "Unexpected estimate: $direction" }
        Write-Output "$direction dry run: $($data.route), estimated $($data.estimated_cost.generations) generation(s)"
        if ($Generate) {
            Write-Output "Submitting $direction"
            $result = & pixellab-cli @common --yes @request
            if ($LASTEXITCODE) { throw "Generation failed for $direction; check ledger for a job ID before retrying" }
            $result | Set-Content "$folder/$direction-result.json" -Encoding UTF8
            Write-Output "$direction complete"
        }
    }
} finally {
    $env:PIXELLAB_ASSUME_YES = $previousAssumeYes
    Pop-Location
}
