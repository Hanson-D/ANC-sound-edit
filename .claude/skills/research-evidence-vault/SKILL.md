---
name: research-evidence-vault
description: Build and maintain local research evidence vaults that combine scholarly literature search, patent/source discovery, mature industry solutions, product/application evidence records, evidence grading, structured JSONL databases, and Markdown reports. Use when the user asks to research a technical/domain question, compare literature with patents or industry applications, create or update a project-specific evidence database, verify source trust levels, or migrate this workflow across agents such as OpenCode, Claude Code, or Codex.
---

# Research Evidence Vault

Use this skill to operate a repository-local research workflow without building a separate UI or agent runtime. Treat the Python CLI as the execution layer, this skill as the portable agent guide, and generated Markdown/JSONL as auditable output.

The skill is domain-agnostic. ANC is only the current sample project at `research-evidence-vault/projects/anc/`.

## Quick Start

Run a project industry/patent/application benchmark:

```bash
.claude/skills/research-evidence-vault/scripts/run_project_industry.sh research-evidence-vault/projects/anc "ANC patents mature solutions product noise isolation curves" "业界 ANC "
```

Verify the workflow:

```bash
.claude/skills/research-evidence-vault/scripts/verify.sh
```

If YAML-aware skill validation or metadata tooling is needed, install helper dependencies first:

```bash
.claude/skills/research-evidence-vault/scripts/install_deps.sh
```

Read project outputs before answering the user:

- `<project-dir>/industry/industry_records.jsonl`
- `<project-dir>/industry/patent_report.md`
- `<project-dir>/industry/solution_product_report.md`
- `<project-dir>/industry/integrated_literature_industry_report.md`

## Project Layout

Each research topic should live under its own project directory:

```text
research-evidence-vault/projects/<project-name>/
  seeds/
    industry_benchmark_seed.json
  industry/
    industry_records.jsonl
    patent_report.md
    solution_product_report.md
    integrated_literature_industry_report.md
```

Use project directories to keep domain fixtures, reports, and evidence databases separate. Do not encode a domain like ANC into the skill name or global workflow contract.

## Workflow

1. Confirm the repository has `research-evidence-vault/tools/lit_workflow.py`.
2. Confirm or create a project directory under `research-evidence-vault/projects/<name>/`.
3. Place industry/patent/application seed data at `<project-dir>/seeds/industry_benchmark_seed.json`.
4. Run `scripts/run_project_industry.sh <project-dir> "<query>" "<topic-label>"`, or call the Python CLI directly.
5. Run `scripts/verify.sh` after changing workflow code, seed data, tests, reports, evidence rules, or skill resources.
6. Summarize outputs with emphasis on evidence distribution, weak sources, source conflicts, and records that need better measurement, official, patent, or primary-source support.
7. Keep the workflow agent-first: prefer CLI, tests, Markdown, and JSONL over adding UI unless the user explicitly asks for a UI.

## Direct Commands

Project industry benchmark:

```bash
python3 research-evidence-vault/tools/lit_workflow.py industry \
  --file research-evidence-vault/projects/anc/seeds/industry_benchmark_seed.json \
  --project-dir research-evidence-vault/projects/anc \
  --topic-label "业界 ANC " \
  --query "ANC patents mature solutions product noise isolation curves"
```

Academic search with industry records:

```bash
python3 research-evidence-vault/tools/lit_workflow.py search \
  --query "psychoacoustic active noise control headphones comfort" \
  --limit 10 \
  --include-industry \
  --industry-seed research-evidence-vault/projects/anc/seeds/industry_benchmark_seed.json \
  --project-dir research-evidence-vault/projects/anc \
  --topic-label "业界 ANC " \
  --industry-scope patents,solutions,products
```

Focused scopes:

```bash
--industry-scope patents
--industry-scope solutions
--industry-scope products
```

## Evidence Rules

Every industry record must preserve:

- `record_type`
- `title`
- `source_url`
- `evidence_level`
- `evidence_basis`

Allowed `record_type` values:

- `patent`
- `solution`
- `product`

Allowed `evidence_level` values:

- `official`
- `measurement`
- `review-derived`
- `inferred`

Read `references/evidence-levels.md` before editing evidence classification logic or seed data.

## Report Contract

Generated reports are knowledge-base artifacts, not legal opinions, experimental plans, or tuning instructions. They may cite patents as public technical entry points, but must not provide infringement analysis or design-around advice.

Read `references/workflow-contract.md` before changing report wording, output paths, tests, or generated file schemas.

## OpenCode Usage

For OpenCode, keep this skill in `.claude/skills/research-evidence-vault/` and add optional `.opencode/commands/<project-command>.md` commands that tell the agent to use this skill, run the project workflow, verify tests, and summarize reports. OpenCode commands should be thin triggers, not second implementations.
