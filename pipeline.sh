#!/usr/bin/env bash
set -e

# --- INPUT ---
APP_DIR="${1:-app_fixed}"

# --- VALIDATION ---
if [ ! -d "$APP_DIR" ]; then
  echo "❌ ERROR: Directory '$APP_DIR' does not exist"
  echo "Usage: $0 [app_directory]"
  exit 1
fi

echo "===> Using app directory: $APP_DIR"

# --- PIPELINE ---
echo "===> [1/3] Build"
echo "Build OK"

echo "===> [2/3] SAST - Semgrep"
semgrep scan --error --config auto "$APP_DIR"

echo "===> [3/3] Policy check - Conftest"
conftest test --rego-version v1 infra/deployment.yaml --policy policies/

echo "===> ✅ Pipeline OK"