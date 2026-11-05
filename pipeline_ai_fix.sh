#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-app}"

# OPENAI_API_KEY is supplied by the environment; never store it in source code.

if [ ! -d "$APP_DIR" ]; then
  echo "❌ ERROR: Directory '$APP_DIR' does not exist"
  echo "Usage: $0 [app_directory]"
  exit 1
fi

echo ""
echo "🚀 Starting AI-assisted pipeline"
echo "📁 App: $APP_DIR"
if [ -n "${OPENAI_API_KEY:-}" ]; then
  echo "🤖 OpenAI mode: enabled"
else
  echo "🤖 OpenAI mode: disabled, deterministic fallback will be used"
fi
echo ""

echo "===> [1/3] SAST - Semgrep"
if semgrep scan --error --config rules/java-sqli-demo.yml "$APP_DIR"; then
  echo "No security findings"
else
  echo ""
  echo "🤖 Findings detected"
  echo "===> [2/3] Running AI fix"
  python3 ai_fix.py "$APP_DIR"

  echo ""
  echo "===> Re-running SAST"
  semgrep scan --error --config rules/java-sqli-demo.yml "$APP_DIR"
fi

echo ""
echo "===> [3/3] Policy check - Conftest"
conftest test --rego-version v1 infra/deployment.yaml --policy policies/

echo ""
echo "✅ Pipeline OK"
