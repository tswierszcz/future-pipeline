#!/usr/bin/env bash
set -euo pipefail

# --- INPUT ---
APP_DIR="${1:-app}"

# --- VALIDATION ---
if [ ! -d "$APP_DIR" ]; then
  echo "❌ ERROR: Directory '$APP_DIR' does not exist"
  echo "Usage: $0 [app_directory]"
  exit 1
fi

echo "===> Using app directory: $APP_DIR"

# --- PIPELINE ---
echo "===> [1/2] SAST - Semgrep"
semgrep scan --error --config rules/ "$APP_DIR"

echo "===> [2/2] Policy check - Conftest"
conftest test --rego-version v1 infra/deployment.yaml --policy policies/

echo "===> ✅ Pipeline OK"
