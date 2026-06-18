# Workflow Contract

The research evidence vault workflow produces local, auditable files under `research-evidence-vault/`.

## Inputs

- `research-evidence-vault/tools/lit_workflow.py`: CLI implementation.
- `research-evidence-vault/projects/<project-name>/seeds/industry_benchmark_seed.json`: project industry benchmark seed.
- `research-evidence-vault/tests/test_lit_workflow_industry.py`: TDD guardrail for industry scope, evidence grades, and report semantics.

## Outputs

- `research-evidence-vault/projects/<project-name>/industry/industry_records.jsonl`
- `research-evidence-vault/projects/<project-name>/industry/patent_report.md`
- `research-evidence-vault/projects/<project-name>/industry/solution_product_report.md`
- `research-evidence-vault/projects/<project-name>/industry/integrated_literature_industry_report.md`

## Required Semantics

- Treat reports as knowledge-base notes.
- Preserve `retrieved_at`, `query`, `source_url`, `evidence_level`, and `evidence_basis` in JSONL records.
- Preserve the distinction between patents, mature solutions, and products.
- Keep product `curve_design` qualitative unless there is a measurement source.
- State evidence levels in generated reports.
- Avoid legal advice, infringement judgments, design-around suggestions, experimental execution plans, and tuning instructions.

## Verification

Install optional validation dependencies when running skill-creator validation or YAML-aware metadata tooling:

```bash
.claude/skills/research-evidence-vault/scripts/install_deps.sh
```

Run:

```bash
.claude/skills/research-evidence-vault/scripts/verify.sh
```

If `py_compile` fails because Python tries to write cache outside the repository, use `PYTHONPYCACHEPREFIX` inside the workspace as shown in the verify script.
