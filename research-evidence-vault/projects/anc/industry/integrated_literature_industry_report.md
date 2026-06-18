---
type: integrated_literature_industry_report
status: knowledge_base_note
---

# 文献与业界 ANC 信息整合报告

Query: `ANC patents mature solutions product noise isolation curves`  
Industry scope: `patent, product, solution`

## 定位

这是知识库整合入口，用来把学术文献 vault 与业界公开信息（专利、方案、上市产品/应用）并排整理。它只做知识库并列索引，不提供实验执行方案、设备参数建议或法律意见。

## 当前业界记录规模

- Patents / patent-family entries: 6
- Mature solution entries: 6
- Product curve-design entries: 23

## 证据等级说明

- `official`: 厂商官方资料、公开支持页、产品页，或公开专利/专利族入口。
- `measurement`: 第三方测试机构或评测库提供的测量/测试页面，适合作为曲线基准入口。
- `review-derived`: 第三方评测、行业新闻或媒体转述，适合做线索但需要复核。
- `inferred`: 从已知产品定位、公开线索或 seed 备注推断，必须人工确认后再用于结论。

## 当前证据等级分布

|evidence_level|count|
|---|---|
|measurement|21|
|official|12|
|review-derived|2|



## 与文献库的连接方式

- 将文献主题、方法、评价指标与专利主题、成熟方案、上市产品/应用记录并排索引。
- 用 `themes`、`knowledge_note`、`evidence_level` 和 `source_url` 建立跨来源连接。
- 对需要数值曲线、参数、法规或法律判断的内容，只保留来源入口和复核提示。

## 知识库维护建议

- 专利记录只作为技术主题和检索入口，不从摘要推断权利要求覆盖范围。
- 每条 industry JSONL 记录必须保留 `evidence_level` 与 `evidence_basis`；前者用于排序可信度，后者说明为什么这样分级。
- 产品/应用设计线索只保留定性描述；如需数值曲线、参数或性能结论，应链接测量来源并单独记录方法版本。
- 上市产品信息变化快，建议每次更新时保留 retrieved_at 和 source_url。
