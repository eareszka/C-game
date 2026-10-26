param([ValidateSet('DryRun','Generate','Balance')][string]$Action = 'DryRun')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$previousAssumeYes = $env:PIXELLAB_ASSUME_YES
Push-Location $root
try {
    $env:PIXELLAB_ASSUME_YES = '0'
    $folder = 'art/enemies/pixellab/32_angont'
    if ($Action -eq 'Balance') {
        & pixellab-cli balance
        if ($LASTEXITCODE) { throw 'Balance query failed.' }
        return
    }
    $prompt = (Get-Content "$folder/prompt.txt" -Raw).Trim()
    $cliArgs = @('--workspace', 'pixellab-out/32-angont-drafts', '--subject', '32-angont', '--json')
    if ($Action -eq 'Generate') { $cliArgs += '--yes' } else { $cliArgs += '--dry-run' }
    $cliArgs += @('edit', "$folder/source_frame0.png", '--prompt', $prompt, '--size', '98x65',
        '--match', 'art/direction/approved_enemy_study/approved_42_fronts_native_512.png',
        '--transparent', '--name', '32-angont-frame0-draft')
    $result = & pixellab-cli @cliArgs
    if ($LASTEXITCODE) { throw 'PixelLab command failed.' }
    if ($Action -eq 'DryRun') {
        $result | Set-Content "$folder/dry-run.json" -Encoding UTF8
        $request = ($result -join "`n") | ConvertFrom-Json
        if (!$request.dry_run -or !$request.arguments.edit_images -or !$request.arguments.reference_image) {
            throw 'Dry run is missing required references.'
        }
        $request | Select-Object dry_run, provider, route, estimated_cost | ConvertTo-Json -Depth 6
    } else { $result }
} finally {
    $env:PIXELLAB_ASSUME_YES = $previousAssumeYes
    Pop-Location
}
