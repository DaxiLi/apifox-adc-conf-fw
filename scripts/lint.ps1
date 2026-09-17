# scripts/lint.ps1 — 本地校验全部配置（不连网关）
# 用法：.\scripts\lint.ps1
Set-Location "$PSScriptRoot\.."               # 锚定仓库根，避免 cwd 依赖
$files = @(
  "configs/global/**/*.yaml",
  "configs/sites/**/*.yaml"
)
$adcArgs = @()
foreach ($f in $files) { $adcArgs += '-f'; $adcArgs += $f }   # -f 逐个重复（adc 的 -f 单值）
# 守卫：只允许 configs/global/** 与 configs/sites/**（防误纳 _templates / 全量 glob）
foreach ($f in $files) {
    if ($f -notmatch '^configs[\\/](global|sites)[\\/]') {
        Write-Error "禁止的配置文件 glob: $f（只允许 configs/global/** 与 configs/sites/**）"; exit 2
    }
}
$adc = if ($env:OS -eq 'Windows_NT') { '.\adc.cmd' } else { './adc' }   # 跨平台入口
& $adc lint @adcArgs
exit $LASTEXITCODE
