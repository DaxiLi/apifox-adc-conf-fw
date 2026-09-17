# scripts/validate.ps1 — 交给后端校验（不落地变更；CI 适用）
# 用法：.\scripts\validate.ps1
Set-Location "$PSScriptRoot\.."
$files = @(
  "configs/global/**/*.yaml",
  "configs/sites/**/*.yaml"
)
$adcArgs = @()
foreach ($f in $files) { $adcArgs += '-f'; $adcArgs += $f }
# 守卫：只允许 configs/global/** 与 configs/sites/**（防误纳 _templates / 全量 glob）
foreach ($f in $files) {
    if ($f -notmatch '^configs[\\/](global|sites)[\\/]') {
        Write-Error "禁止的配置文件 glob: $f（只允许 configs/global/** 与 configs/sites/**）"; exit 2
    }
}
$adc = if ($env:OS -eq 'Windows_NT') { '.\adc.cmd' } else { './adc' }   # 跨平台入口
& $adc validate @adcArgs --timeout 60s
exit $LASTEXITCODE
