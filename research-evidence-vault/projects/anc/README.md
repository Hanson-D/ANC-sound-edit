# ANC Research Project

This project is the current benchmark topic for the generic research evidence vault workflow.

ANC-specific seed data lives in:

- `seeds/industry_benchmark_seed.json`

Generated industry/patent/application reports are written to:

- `industry/industry_records.jsonl`
- `industry/patent_report.md`
- `industry/solution_product_report.md`
- `industry/integrated_literature_industry_report.md`

Run from the repository root:

```bash
.claude/skills/research-evidence-vault/scripts/run_project_industry.sh research-evidence-vault/projects/anc "ANC patents mature solutions product noise isolation curves" "业界 ANC "
```
