#!/usr/bin/env bash
# 本地校验全部配置（不连网关）—— Linux/macOS 原生入口
# 用法：./scripts/lint.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FILES=(-f "configs/global/**/*.yaml" -f "configs/sites/**/*.yaml")

# 守卫：只允许 configs/global/** 与 configs/sites/**（防误纳 _templates / 全量 glob）
for f in "${FILES[@]}"; do
  case "$f" in
    -f|--*) continue ;;
  esac
  case "${f#configs/}" in
    global/*|sites/*) ;;
    *) echo "禁止的配置文件 glob: $f（只允许 configs/global/** 与 configs/sites/**）" >&2; exit 2 ;;
  esac
done

exec "$ROOT/adc" lint "${FILES[@]}"
