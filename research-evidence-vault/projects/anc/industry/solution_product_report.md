---
type: industry_solution_product_report
status: knowledge_base_note
---

# 业界 ANC 方案与产品知识库报告

Query: `ANC patents mature solutions product noise isolation curves`

## 证据等级说明

- `official`: 厂商官方资料、公开支持页、产品页，或公开专利/专利族入口。
- `measurement`: 第三方测试机构或评测库提供的测量/测试页面，适合作为曲线基准入口。
- `review-derived`: 第三方评测、行业新闻或媒体转述，适合做线索但需要复核。
- `inferred`: 从已知产品定位、公开线索或 seed 备注推断，必须人工确认后再用于结论。

## 当前证据等级分布

|evidence_level|count|
|---|---|
|measurement|21|
|official|6|
|review-derived|2|

## 成熟方案/公开技术叙述

|year|organization|title|themes|knowledge_note|evidence_level|evidence_basis|source_url|
|---|---|---|---|---|---|---|---|
|2023|Apple|Apple Adaptive Audio / Adaptive Noise Control|adaptive mode, ANC transparency blend, environment awareness|Apple documents Adaptive mode as blending ANC and Transparency based on changing noise conditions.|official|official Apple public product/support material|https://support.apple.com/en-us/104979|
|2025|Sony|Sony Adaptive NC Optimizer / Dual Noise Sensor product approach|adaptive optimizer, external noise, air pressure, fit|Sony product materials describe adaptive noise-cancelling optimization using external noise, air pressure, and fit factors.|official|official Sony public product/support material|https://electronics.sony.com/audio/headphones/headband/p/wh1000xm6-p|
|2023|Bose|Bose CustomTune / QuietComfort adaptive ANC approach|CustomTune, personalized ANC, comfort|Bose QC Ultra reviews describe CustomTune technology adjusting sound profile and noise cancelling for user/environment.|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/bose/quietcomfort-ultra-headphones-wireless|
|2024|Bose|Bose ANC explainer: two microphones and anti-noise|two microphones, anti-noise, consumer explanation|Bose public explainer states ANC headphones read/analyze outside sounds and emit opposite signals.|official|official Bose public product/support material|https://www.bose.com/stories/what-is-active-noise-cancellation|
|2020|Sony|Sony WH-1000XM4 Dual Noise Sensor and QN1 architecture|dual noise sensor, QN1, SoC sensing, adaptive sound control|AudioXpress summarizes Sony WH-1000XM4 architecture with microphones, Dual Noise Sensor, QN1, and SoC sensing.|review-derived|third-party review or industry-news article|https://audioxpress.com/news/sony-launches-new-wh-1000xm4-headphones-with-next-generation-adaptive-noise-canceling|
|2026|RTINGS|RTINGS headphone noise isolation measurement methodology|measurement, common scenarios, airplane office street|RTINGS methodology and common-scenario graphs are useful for product curve benchmarking.|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/tests/noise-isolation-cancellation-passive-active|

## 产品与应用/产品设计线索（定性）

这些记录是产品/应用级设计线索，不替代第三方测量曲线、厂商私有算法或工程实现细节。

|organization|title|product_form|curve_design|evidence_level|evidence_basis|source_url|
|---|---|---|---|---|---|---|
|Sony|Sony WH-1000XM5|over-ear|broadband premium ANC; strong low-frequency travel-noise attenuation plus meaningful mid/high isolation from sealed over-ear design; benchmark against Bose QC Ultra in reviews|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/sony/wh-1000xm5-wireless|
|Sony|Sony WH-1000XM6|over-ear|adaptive NC optimizer product design; marketed as adjusting to external noise, air pressure and fit, implying curve adaptation by context rather than a fixed attenuation curve|official|official Sony public product/support material|https://electronics.sony.com/audio/headphones/headband/p/wh1000xm6-p|
|Sony|Sony WH-1000XM4|over-ear|mature hybrid over-ear ANC family; comparison material useful for evolution of low-frequency and overall isolation across XM generations|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/learn/sony-xm-series-comparison|
|Bose|Bose QuietComfort Ultra Headphones|over-ear|comfort-forward premium over-ear ANC; reviews describe slight edge in noise isolation versus WH-1000XM5 and CustomTune adaptation|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/bose/quietcomfort-ultra-headphones-wireless|
|Bose|Bose QuietComfort Ultra Headphones 2nd Gen|over-ear|adaptive ANC and passive isolation emphasized for bus rumble and plane cabin din; curve benchmark for travel-noise reduction|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/bose/quietcomfort-ultra-headphones-2nd-gen|
|Bose|Bose QuietComfort Headphones|over-ear|classic comfort ANC product with Quiet/Aware modes and customizable listening modes; benchmark for comfort-oriented but less flagship curve design|official|official Bose public product/support material|https://www.bose.com/p/headphones/quietcomfort-acoustic-noise-cancelling-headphones/QC-HEADPHONEARN.html|
|Apple|Apple AirPods Pro 2|in-ear TWS|remarkable in-ear ANC; RTINGS describes strong attenuation from fridge compressors to raspy exhausts, combining seal-dependent passive high-frequency isolation with ANC low-frequency reduction|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/apple/airpods-pro-2nd-generation-truly-wireless|
|Apple|Apple AirPods Pro 3|in-ear TWS|RTINGS comparison states superior noise isolation versus AirPods Pro 2 with hybrid silicone-and-foam tips and deeper fit aiding high-frequency isolation|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/learn/apple-airpods-pro-gen-2-vs-airpods-pro-gen-3|
|Apple|Apple AirPods Max|over-ear|over-ear ANC with mode switching and Adaptive Audio support in newer generation; benchmark for ecosystem-controlled ANC/transparency mode design|official|official Apple public product/support material|https://support.apple.com/en-us/108918|
|Bose|Bose QuietComfort Ultra Earbuds|in-ear TWS|in-ear flagship ANC with CustomTune-like personalization; curve expected to combine strong low-frequency ANC and eartip-dependent high-frequency isolation|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/bose/quietcomfort-ultra-earbuds-truly-wireless|
|Samsung|Samsung Galaxy Buds3 Pro|in-ear TWS|adaptive TWS ANC benchmark; useful for studying product curves where fit and eartip seal dominate high-frequency isolation|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/samsung/galaxy-buds3-pro-true-wireless|
|Samsung|Samsung Galaxy Buds2 Pro|in-ear TWS|compact TWS ANC benchmark; likely curve archetype is stronger low-frequency active reduction with seal-dependent upper-band isolation|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/samsung/galaxy-buds2-pro-true-wireless|
|Sennheiser|Sennheiser Momentum 4 Wireless|over-ear|premium over-ear ANC but reviews compare it behind Bose QC Ultra for noise isolation; benchmark for sound-quality-first tuning versus maximum ANC|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/sennheiser/momentum-4-wireless|
|Sennheiser|Sennheiser Momentum True Wireless 4|in-ear TWS|premium TWS ANC benchmark; useful for comparing adaptive ANC and passive seal in a sound-quality-oriented product|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/sennheiser/momentum-true-wireless-4|
|Anker Soundcore|Anker Soundcore Space Q45|over-ear|value over-ear ANC benchmark; useful for contrast between cost-sensitive ANC curve and premium products|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/anker/soundcore-space-q45-wireless|
|Anker Soundcore|Anker Soundcore Liberty 4 NC|in-ear TWS|value TWS ANC benchmark; eartip seal plus adaptive ANC curve useful for budget-product comparison|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/anker/soundcore-liberty-4-nc-truly-wireless|
|Jabra|Jabra Elite 10 Gen 2|in-ear TWS|semi-open comfort-oriented TWS ANC; benchmark for comfort/fit tradeoff where passive high-frequency isolation may be lower than deep-seal earbuds|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/jabra/elite-10-gen-2-true-wireless|
|Jabra|Jabra Elite 8 Active Gen 2|in-ear TWS|sport TWS ANC benchmark; curve design must balance occlusion/comfort, seal robustness, and wind/outdoor noise|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/jabra/elite-8-active-gen-2-true-wireless|
|Google|Google Pixel Buds Pro 2|in-ear TWS|adaptive TWS ANC benchmark within Android ecosystem; relevant for fit-dependent curve adaptation and transparency interactions|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/google/pixel-buds-pro-2-truly-wireless|
|Nothing|Nothing Headphone (1)|over-ear|new entrant over-ear ANC benchmark; comparison coverage positions ANC as solid but below Sony WH-1000XM5, useful for maturity-gap analysis|review-derived|third-party review or industry-news article|https://www.tomsguide.com/audio/over-ear-headphones/nothing-headphones-1-vs-sony-wh-1000xm5-which-noise-cancelling-headphones-win|
|Bowers & Wilkins|Bowers & Wilkins Px7 S3|over-ear|premium over-ear ANC with sound-quality emphasis; benchmark for less aggressive but comfortable ANC curve design|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/bowers-wilkins/px7-s3-wireless|
|Shure|Shure AONIC 50 Gen 2|over-ear|studio-oriented over-ear ANC benchmark; useful for comparing sound-quality/monitoring priorities against ANC depth|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/shure/aonic-50-gen-2-wireless|
|Technics|Technics EAH-AZ100|in-ear TWS|premium TWS ANC benchmark; useful for curve comparison among compact in-ear products with adaptive cancellation|measurement|third-party headphone noise-isolation measurement/review source|https://www.rtings.com/headphones/reviews/technics/eah-az100-true-wireless|
