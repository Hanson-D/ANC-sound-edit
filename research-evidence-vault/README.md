# Research Vault 文献工作流

这是一个面向 Codex / 本地 agent 的文献检索、拉取、阅读总结、知识库整理与综述报告生成工具链。

## 原则

- 只使用公开 API 与开放合法 PDF 链接；不绕过付费墙。
- 不编造 DOI、作者、结果或引用；未知字段保留为空或标记 `unknown`。
- 如果只能获得摘要，阅读笔记会标记“基于摘要总结”。
- 综述报告区分“证据支持”“推测”“研究空白”。
- Markdown + YAML frontmatter 兼容 Obsidian，并尽量保持 OKF 风格的人类可读、agent 可解析结构。

## 快速开始

```bash
python research-evidence-vault/tools/lit_workflow.py search --query "active noise control adaptive filtering" --limit 10
python research-evidence-vault/tools/lit_workflow.py ingest --file research-evidence-vault/seeds/anc_comfort_bark_seed.json --query "ANC comfort Bark loudness spectral modulation"
python research-evidence-vault/tools/lit_workflow.py fetch
python research-evidence-vault/tools/lit_workflow.py summarize --all
python research-evidence-vault/tools/lit_workflow.py organize
python research-evidence-vault/tools/lit_workflow.py matrix
python research-evidence-vault/tools/lit_workflow.py report
python research-evidence-vault/tools/lit_workflow.py update --query "your new query" --limit 10
```

## 命令

- `search`: 根据主题/关键词/研究问题/种子 ID 检索 arXiv、PubMed、Semantic Scholar、OpenAlex、Crossref、bioRxiv/medRxiv，并保存 JSONL 结果与搜索日志。
- `ingest`: 在网络/API 受限时导入人工核对过的 JSON/JSONL 种子记录，仍走后续 fetch/summarize/organize/matrix/report 流水线。
- `fetch`: 标准化元数据，按论文生成目录；如发现开放 PDF，下载到 `paper.pdf`。
- `summarize`: 对单篇或全部论文生成结构化阅读笔记；没有全文时明确标注基于摘要。
- `organize`: 去重、生成 paper note、主题/方法/理论索引、OKF/Obsidian 友好 Markdown。
- `matrix`: 生成 evidence matrix、method matrix、gap matrix、核心发现与争议点表。
- `report`: 生成综述报告与 executive summary。
- `update`: search → fetch → summarize → organize → matrix → report 的增量流水线。

## 文件结构

见项目根目录下 `research-evidence-vault/`。每篇论文位于 `papers/YYYY_FirstAuthor_ShortTitle/`，包含 `metadata.yaml`、`paper.md`、`summary.md`、`critique.md`、`quotes.md`、`fulltext.txt` 以及可选 `paper.pdf`。


## 业界信息入口

如果需要把业界成熟方案、公开专利和上市产品 ANC 曲线设计线索纳入知识库，可在检索时增加：

```bash
python research-evidence-vault/tools/lit_workflow.py search --query "ANC comfort Bark" --include-industry --industry-scope all
```

也可以只跑业界基准种子，不触发学术 API：

```bash
python research-evidence-vault/tools/lit_workflow.py industry --file research-evidence-vault/seeds/industry_anc_benchmark_seed.json --query "ANC patents mature solutions product noise isolation curves"
```

`--industry-scope` 支持 `all`、`patents`、`solutions`、`products` 或逗号组合。输出位于 `research-evidence-vault/industry/`，包括专利报告、方案与产品报告、以及文献/业界整合报告。
