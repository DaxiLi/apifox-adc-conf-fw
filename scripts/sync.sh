#!/usr/bin/env bash
# 全量同步（⚠️ 作用域外的资源会被删除）—— Linux/macOS 原生入口
# 用法：
#   ./scripts/sync.sh                 # lint → diff → 输入 YES 确认 → sync
#   ./scripts/sync.sh --yes           # 跳过确认（CI/自动化慎用）
#   ./scripts/sync.sh --skip-lint     # 跳过 lint
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

YES=0
SKIP_LINT=0
for arg in "$@"; do
  case "$arg" in
    --yes)       YES=1 ;;
    --skip-lint) SKIP_LINT=1 ;;
    *) echo "未知参数: $arg" >&2; exit 2 ;;
  esac
done

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

if [ "$SKIP_LINT" != "1" ]; then
  "$ROOT/adc" lint "${FILES[@]}"
fi
"$ROOT/adc" diff "${FILES[@]}" --timeout 60s
if [ "$YES" != "1" ]; then
  read -r -p "diff 确认无误？输入 YES 后执行 sync: " ans
  if [ "$ans" != "YES" ]; then echo "已取消"; exit 1; fi
fi
exec "$ROOT/adc" sync "${FILES[@]}" --timeout 60s
