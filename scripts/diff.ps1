# scripts/diff.ps1 — 本地 vs 网关差异（只读；同步前必看）
# 用法：.\scripts\diff.ps1
Set-Location "$PSScriptRoot\.."
$files = @(
  "configs/global/**/*.yaml",
  "configs/sites/**/*.yaml"
)
$adcArgs = @()
foreach ($f in $files) { $adcArgs += '-f'; $adcArgs += $f }
$adc = if ($env:OS -eq 'Windows_NT') { '.\adc.cmd' } else { './adc' }   # 跨平台入口
& $adc diff @adcArgs --timeout 60s
exit $LASTEXITCODE
