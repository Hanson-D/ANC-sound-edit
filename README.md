# ancadjust

Local workspace for research evidence collection, patent / industry application tracking, and evidence-graded database/report generation.

## Main Tool

- `research-evidence-vault/`: generic literature, patent, industry solution, product/application evidence vault workflow.
- `.claude/skills/research-evidence-vault/`: portable Agent skill wrapper for OpenCode, Claude Code, Codex, and similar agents.

## Current Project

- `research-evidence-vault/projects/anc/`: ANC benchmark project used to validate the workflow.

Run from this directory:

```bash
.claude/skills/research-evidence-vault/scripts/run_project_industry.sh research-evidence-vault/projects/anc "ANC patents mature solutions product noise isolation curves" "业界 ANC "
```

Verify:

```bash
.claude/skills/research-evidence-vault/scripts/verify.sh
```
