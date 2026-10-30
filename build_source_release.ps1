param([switch]$IncludeUnverifiedMusic)
$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$releaseDirectory = Join-Path $projectDirectory 'dist'
New-Item -ItemType Directory -Path $releaseDirectory -Force | Out-Null
$stagingDirectory = Join-Path $releaseDirectory ('staging-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stagingDirectory | Out-Null
foreach ($filename in @('fps_game.py','rogue_content.py','requirements.txt','RELEASE_GUIDE.md','UPGRADE_GUIDE.md','CHANGELOG.md','ART_LICENSES.md')) {
    Copy-Item -LiteralPath (Join-Path $projectDirectory $filename) -Destination $stagingDirectory
}
if ($IncludeUnverifiedMusic) {
    $audioDirectory = Join-Path $stagingDirectory 'assets\audio'
    New-Item -ItemType Directory -Path $audioDirectory -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectDirectory 'assets\audio\kiravale-gaming-music-593659.mp3') -Destination $audioDirectory
}
$archivePath = Join-Path $releaseDirectory ('RogueFPS-0.2.0-source-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
Compress-Archive -Path (Join-Path $stagingDirectory '*') -DestinationPath $archivePath
Get-FileHash -LiteralPath $archivePath -Algorithm SHA256
Write-Output "Source package: $archivePath"
Write-Output "Staging retained: $stagingDirectory"
