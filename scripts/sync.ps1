# scripts/sync.ps1 — 全量同步（⚠️ 作用域外的资源会被删除）
# 用法：.\scripts\sync.ps1 [-SkipLint] [-Yes]
#   -SkipLint  跳过 lint；-Yes 跳过 YES 确认直接 sync
# 流程：lint → diff → 输入 YES 确认 → sync
param([switch]$SkipLint, [switch]$Yes)
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
if (-not $SkipLint) { & $adc lint @adcArgs; if ($LASTEXITCODE -ne 0) { Write-Host 'lint 失败，已中止 sync' -ForegroundColor Red; exit 1 } }
& $adc diff @adcArgs --timeout 60s
if (-not $Yes) {
  $ans = Read-Host "diff 确认无误？输入 YES 后执行 sync"
  if ($ans -ne 'YES') { Write-Host '已取消' -ForegroundColor Yellow; exit 1 }
}
& $adc sync @adcArgs --timeout 60s
exit $LASTEXITCODE
