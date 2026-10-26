param([switch]$Generate)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$previousAssumeYes = $env:PIXELLAB_ASSUME_YES
Push-Location $root
try {
    $env:PIXELLAB_ASSUME_YES = '0'
    $folder = 'art/enemies/pixellab/66_ayotochtli'
    if ($Generate -and (Test-Path "$folder/result.json")) { throw 'A draft already exists; review it before requesting another generation' }
    $prompt = (Get-Content "$folder/prompt.txt" -Raw).Trim()
    $common = @('--json', '--workspace', 'pixellab-out/66-ayotochtli-drafts', '--subject', '66-ayotochtli')
    $request = @('edit', "$folder/source_frame0.png", '--prompt', $prompt, '--size', '48x35',
        '--match', 'art/direction/approved_enemy_study/approved_42_fronts_native_512.png',
        '--transparent', '--name', '66-ayotochtli-frame0-draft')
    $dry = & pixellab-cli @common --dry-run @request
    if ($LASTEXITCODE) { throw 'Dry run failed' }
    $dry | Set-Content "$folder/dry-run.json" -Encoding UTF8
    $data = ($dry -join "`n") | ConvertFrom-Json
    if (!$data.dry_run -or !$data.arguments.edit_images -or !$data.arguments.reference_image -or $data.estimated_cost.generations -gt 30) {
        throw 'Unexpected request or estimate'
    }
    Write-Output "Dry run validated: $($data.route), estimated $($data.estimated_cost.generations) generations, source and approved style reference included"
    if ($Generate) {
        $result = & pixellab-cli @common --yes @request
        if ($LASTEXITCODE) { throw 'Generation failed; inspect ledger for a job ID before retrying' }
        $result | Set-Content "$folder/result.json" -Encoding UTF8
        $result
    }
} finally {
    $env:PIXELLAB_ASSUME_YES = $previousAssumeYes
    Pop-Location
}
