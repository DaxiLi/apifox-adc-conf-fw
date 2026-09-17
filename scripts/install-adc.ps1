<#
.SYNOPSIS
    安装/升级 ADC（API Declarative CLI）到 .bin/adc/。

.DESCRIPTION
    从 GitHub Releases 下载对应平台/架构的 ADC 二进制到 .bin/adc/。
    兼容 Windows PowerShell 与 PowerShell Core（pwsh，Linux/macOS）。
    已安装同版本时默认跳过；-Force 强制重下。

.PARAMETER Version
    要安装的版本（默认 latest）。可写 0.30.3 或 v0.30.3。

.PARAMETER Force
    同版本也重新下载覆盖。

.PARAMETER Repo
    下载源仓库，默认 api7/adc。

.EXAMPLE
    .\scripts\install-adc.ps1            # 安装最新版
    ./scripts/install-adc.ps1 -Version 0.30.3   # 安装指定版本
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Version = 'latest',
    [switch]$Force,
    [string]$Repo = 'api7/adc'
)

$ErrorActionPreference = 'Stop'
$root   = Split-Path -Parent $PSScriptRoot
$destDir = Join-Path $root '.bin/adc'

function Get-OsArch {
    $isWin = $env:OS -eq 'Windows_NT'
    if ($isWin) {
        $os = 'windows'
        switch ($env:PROCESSOR_ARCHITECTURE) {
            'AMD64' { $arch = 'amd64' }
            'ARM64' { $arch = 'arm64' }
            default { throw "不支持的架构: $env:PROCESSOR_ARCHITECTURE" }
        }
    } else {
        $kernel = (& uname -s).Trim()
        if ($kernel -eq 'Darwin') { $os = 'darwin' }
        elseif ($kernel -eq 'Linux') { $os = 'linux' }
        else { throw "不支持的系统: $kernel" }
        $mach = (& uname -m).Trim()
        switch ($mach) {
            { $_ -in @('x86_64', 'amd64') }  { $arch = 'amd64' }
            { $_ -in @('aarch64', 'arm64') } { $arch = 'arm64' }
            default { throw "不支持的架构: $mach" }
        }
    }
    return @{ os = $os; arch = $arch; isWin = $isWin }
}

function Get-LatestTag {
    $api = "https://api.github.com/repos/$Repo/releases/latest"
    $h = @{ 'User-Agent' = 'install-adc.ps1'; 'Accept' = 'application/vnd.github+json' }
    $r = Invoke-RestMethod -Uri $api -Headers $h -TimeoutSec 30
    return $r.tag_name
}

function Get-FileViaCurl([string]$url, [string]$out) {
    $curl = if ($env:OS -eq 'Windows_NT') { 'curl.exe' } else { 'curl' }
    & $curl -sS -L --fail --retry 3 --max-time 300 -o $out $url
    if ($LASTEXITCODE -ne 0) { throw "curl 下载失败: $url" }
}

$info  = Get-OsArch
$os    = $info.os
$arch  = $info.arch
$isWin = $info.isWin

if ($Version -eq 'latest') { $Version = (Get-LatestTag).TrimStart('v') }
else                       { $Version = $Version.TrimStart('v') }

$tag    = "v$Version"
$ext    = if ($isWin) { 'zip' } else { 'tar.gz' }
$asset  = "adc_${Version}_${os}_${arch}.$ext"
$url    = "https://github.com/$Repo/releases/download/$tag/$asset"
$binName = if ($isWin) { 'adc.exe' } else { 'adc' }
$destBin = Join-Path $destDir $binName

if (-not $Force -and (Test-Path $destBin)) {
    $installed = (& $destBin --version 2>$null | Select-Object -First 1)
    if ($installed -match [regex]::Escape($Version)) {
        Write-Host "已安装 adc $Version，跳过（-Force 强制重装）"
        exit 0
    }
}

if ($PSCmdlet.ShouldProcess($url, "下载并安装 adc $Version ($os/$arch)")) {
    $tmp = Join-Path $env:TEMP "adc-install-$PID"
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    try {
        $archive = Join-Path $tmp $asset
        Write-Host "下载 $url ..."
        # 优先 curl.exe（Windows 10+ 自带、Linux/macOS 自带）；失败回退 Invoke-WebRequest
        try { Get-FileViaCurl $url $archive }
        catch {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing -TimeoutSec 300
        }
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        if ($isWin) {
            Expand-Archive -Path $archive -DestinationPath $tmp -Force
            Copy-Item (Join-Path $tmp $binName) $destBin -Force
        } else {
            tar -xzf $archive -C $tmp
            Copy-Item (Join-Path $tmp $binName) $destBin -Force
            chmod +x $destBin
        }
        Write-Host "已安装: $destBin"
        & $destBin --version
    } finally {
        Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    }
}
