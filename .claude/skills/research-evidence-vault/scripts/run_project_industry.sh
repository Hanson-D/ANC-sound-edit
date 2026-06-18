#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

PROJECT_DIR="${1:-research-evidence-vault/projects/anc}"
QUERY="${2:-ANC patents mature solutions product noise isolation curves}"
TOPIC_LABEL="${3:-业界 ANC }"
SEED_FILE="${4:-$PROJECT_DIR/seeds/industry_benchmark_seed.json}"

python3 research-evidence-vault/tools/lit_workflow.py industry \
  --file "$SEED_FILE" \
  --project-dir "$PROJECT_DIR" \
  --topic-label "$TOPIC_LABEL" \
  --query "$QUERY"
