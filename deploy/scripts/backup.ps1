param(
  [string]$OutputDirectory = ".\backups"
)

$ErrorActionPreference = "Stop"
$resolvedRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$targetDirectory = [IO.Path]::GetFullPath((Join-Path $resolvedRoot $OutputDirectory))
New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $targetDirectory "rovia-$stamp.sql"
docker compose -f (Join-Path $resolvedRoot "docker-compose.yml") exec -T postgres pg_dump -U rovia -d rovia --clean --if-exists | Out-File -FilePath $target -Encoding utf8
Get-Item -LiteralPath $target | Select-Object FullName, Length, LastWriteTime
