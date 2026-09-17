# scripts/diff.ps1 — 本地 vs 网关差异（只读；同步前必看）
# 用法：.\scripts\diff.ps1
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
& $adc diff @adcArgs --timeout 60s
exit $LASTEXITCODE
