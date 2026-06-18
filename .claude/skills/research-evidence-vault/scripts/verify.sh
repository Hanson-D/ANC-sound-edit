#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

python3 -m unittest research-evidence-vault/tests/test_lit_workflow_industry.py
PYTHONPYCACHEPREFIX="$ROOT/.pycache" python3 -m py_compile research-evidence-vault/tools/lit_workflow.py
