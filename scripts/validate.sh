#!/usr/bin/env bash
# 交给后端校验（不落地变更；CI 适用）—— Linux/macOS 原生入口
# 用法：./scripts/validate.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec "$ROOT/adc" validate -f "configs/global/**/*.yaml" -f "configs/sites/**/*.yaml" --timeout 60s
