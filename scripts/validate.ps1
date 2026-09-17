# scripts/validate.ps1 — 交给后端校验（不落地变更；CI 适用）
# 用法：.\scripts\validate.ps1
Set-Location "$PSScriptRoot\.."
$files = @(
  "configs/global/**/*.yaml",
  "configs/sites/**/*.yaml"
)
$adcArgs = @()
foreach ($f in $files) { $adcArgs += '-f'; $adcArgs += $f }
$adc = if ($env:OS -eq 'Windows_NT') { '.\adc.cmd' } else { './adc' }   # 跨平台入口
& $adc validate @adcArgs --timeout 60s
exit $LASTEXITCODE
