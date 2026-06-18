#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

python3 -m pip install -r .claude/skills/research-evidence-vault/requirements.txt
