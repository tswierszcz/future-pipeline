#!/usr/bin/env bash
set -e

APP_DIR="${1:-app}"

if [ ! -d "$APP_DIR" ]; then
  echo "❌ ERROR: Directory '$APP_DIR' does not exist"
  echo "Usage: $0 [app_directory]"
  exit 1
fi

echo ""
echo "🚀 Starting pipeline"
echo "📁 App: $APP_DIR"
echo ""

echo "===> [1/3] Build"
echo "Build OK"

echo "===> [2/3] SAST - Semgrep"
#semgrep scan --error --config rules/java-sqli-demo.yml "$APP_DIR"
semgrep scan --error --config auto "$APP_DIR"

echo "===> [3/3] Policy check - Conftest"
conftest test --rego-version v1 infra/deployment.yaml --policy policies/

echo ""
echo "✅ Pipeline OK"
