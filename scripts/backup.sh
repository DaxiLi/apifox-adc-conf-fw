#!/usr/bin/env bash
# 导出网关配置基线备份（只读；含 --with-id 保留资源 ID）—— Linux/macOS 入口
# 用法：./scripts/backup.sh [输出目录，默认 backups]
# 注意：备份可能包含消费者密钥等敏感信息，backups/ 已在 .gitignore 中，勿提交
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT_DIR="${1:-backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$OUT_DIR/adc-baseline-$STAMP.yaml"
"$ROOT/adc" dump --with-id -o "$OUT" --timeout 60s
echo "基线已备份: $OUT"
