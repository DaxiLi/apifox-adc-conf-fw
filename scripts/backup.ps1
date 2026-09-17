# scripts/backup.ps1 — 导出网关配置基线备份（只读；含 --with-id 保留资源 ID）
# 用法：.\scripts\backup.ps1 [-OutDir .\backups]
# 注意：备份可能包含消费者密钥等敏感信息，backups/ 已在 .gitignore 中，勿提交
param([string]$OutDir = 'backups')
Set-Location "$PSScriptRoot\.."
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = Join-Path $OutDir "adc-baseline-$stamp.yaml"
$adc = if ($env:OS -eq 'Windows_NT') { '.\adc.cmd' } else { './adc' }
& $adc dump --with-id -o $out --timeout 60s
if ($LASTEXITCODE -eq 0) { Write-Host "基线已备份: $out" }
exit $LASTEXITCODE
