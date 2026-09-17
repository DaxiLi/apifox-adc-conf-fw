#!/usr/bin/env bash
# 本地校验全部配置（不连网关）—— Linux/macOS 原生入口
# 用法：./scripts/lint.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec "$ROOT/adc" lint -f "configs/global/**/*.yaml" -f "configs/sites/**/*.yaml"
