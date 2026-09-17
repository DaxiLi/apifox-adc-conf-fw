#!/usr/bin/env bash
# 安装/升级 ADC（API Declarative CLI）到 .bin/adc/（Linux / macOS）
# 用法：
#   ./scripts/install-adc.sh                # 安装最新版
#   ./scripts/install-adc.sh 0.30.3         # 安装指定版本
#   ./scripts/install-adc.sh latest --force # 强制重装
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$ROOT/.bin/adc"
VERSION="latest"
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --force|-f) FORCE=1 ;;
    -*) echo "未知参数: $arg" >&2; exit 2 ;;
    *) VERSION="$arg" ;;
  esac
done

OS="$(uname -s)"
case "$OS" in
  Darwin) OS="darwin" ;;
  Linux)  OS="linux" ;;
  *) echo "不支持的系统: $OS" >&2; exit 1 ;;
esac

MACHINE="$(uname -m)"
case "$MACHINE" in
  x86_64|amd64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "不支持的架构: $MACHINE" >&2; exit 1 ;;
esac

if [ "$VERSION" = "latest" ]; then
  VERSION="$(curl -fsSL "https://api.github.com/repos/api7/adc/releases/latest" \
    | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"v\([^"]*\)".*/\1/p')"
  [ -n "$VERSION" ] || { echo "无法解析最新版本号" >&2; exit 1; }
fi
VERSION="${VERSION#v}"
TAG="v$VERSION"
ASSET="adc_${VERSION}_${OS}_${ARCH}.tar.gz"
URL="https://github.com/api7/adc/releases/download/${TAG}/${ASSET}"

BIN="$DEST_DIR/adc"
if [ "$FORCE" != "1" ] && [ -x "$BIN" ]; then
  CURRENT="$("$BIN" --version 2>/dev/null | head -n1 || true)"
  if printf '%s' "$CURRENT" | grep -qF "$VERSION"; then
    echo "已安装 adc $VERSION，跳过（--force 强制重装）"
    exit 0
  fi
fi

echo "下载 $URL"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL --retry 3 -o "$TMP/$ASSET" "$URL"
mkdir -p "$DEST_DIR"
tar -xzf "$TMP/$ASSET" -C "$TMP"
install -m 0755 "$TMP/adc" "$BIN"
echo "已安装: $BIN"
"$BIN" --version
