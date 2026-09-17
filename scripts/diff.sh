#!/usr/bin/env bash
# 本地 vs 网关差异（只读；同步前必看）—— Linux/macOS 原生入口
# 用法：./scripts/diff.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec "$ROOT/adc" diff -f "configs/global/**/*.yaml" -f "configs/sites/**/*.yaml" --timeout 60s
