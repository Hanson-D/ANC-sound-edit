---
type: integrated_literature_industry_report
status: knowledge_base_note
---

# 文献与业界 ANC 信息整合报告

Query: `ANC patents mature solutions product noise isolation curves`  
Industry scope: `patent, product, solution`

## 定位

这是知识库整合入口，用来把学术文献 vault 与业界公开信息（专利、方案、上市产品）并排整理。它只做知识库并列索引，不提供实验执行方案、设备参数建议或法律意见。

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

- `psychoacoustic-anc` ↔ 产品中的 adaptive ANC / CustomTune / Adaptive Audio。
- `residual-noise-shaping` ↔ 产品中的 curve_design 定性描述与第三方 noise-isolation graphs。
- `headphone-anc` / `pnc-fixed` ↔ 专利中的麦克风、腔体、vent、fit、air-pressure、seal 约束。
- `specific-loudness` / `sharpness` / `roughness` ↔ 产品评价中的 comfort、hiss、travel rumble、office/street scenarios。

## 知识库维护建议

- 专利记录只作为技术主题和检索入口，不从摘要推断权利要求覆盖范围。
- 每条 industry JSONL 记录必须保留 `evidence_level` 与 `evidence_basis`；前者用于排序可信度，后者说明为什么这样分级。
- 产品 curve_design 只保留定性曲线线索；如需数值曲线，应链接 RTINGS/SoundGuys 等测量图并单独记录方法版本。
- 上市产品信息变化快，建议每次更新时保留 retrieved_at 和 source_url。
