# 半入耳 ANC 体验问题：文献缺口与补充线索

date: 2026-06-25

## 当前 corpus 覆盖情况

工作目录已有材料主要覆盖：

- psychoacoustic ANC：A-weighting、ITU-R 468、pleasantness、loudness、roughness、sharpness；
- residual noise shaping / active noise equalization；
- Bark / critical band / specific loudness；
- headphone / near-ear ANC 的若干算法与综述；
- 产品与专利基准入口。

这些材料足以支持一个主结论：**ANC comfort 不能只看总降噪量或局部深度，残余谱形和心理声学指标也需要单独看。**

但对“半入耳式像 AirPods 4，1-2 kHz 比竞品弱、500-1000 Hz 和 2-4 kHz 更深却更闷/耳压更强”这个问题，还缺四类更直接的文献。

## 需要补的文献簇

### 1. Open / vented fitting 与 occlusion effect

用途：解释半入耳或浅插入结构为什么容易出现“堵、闷、自声、耳压感”，以及为什么开孔/开放佩戴会缓解但同时削弱 ANC 可控性。

建议补入：

- Winkler, A., Latzel, M., & Holube, I. (2016). **Open Versus Closed Hearing-Aid Fittings: A Literature Review**. *Trends in Hearing*.
- Stenfelt, S., & Reinfeldt, S. (2007). **A model of the occlusion effect with bone-conducted stimulation**. *International Journal of Audiology*.
- Zurbrugg, T., Stirnemann, A., Kuster, M., & Lissek, H. (2014). **Investigations on the physical factors influencing the ear canal occlusion effect caused by hearing aids**. *Acta Acustica united with Acustica*.
- Carillo, K., Doutres, O., & Sgard, F. (2020). **Theoretical investigation of the low frequency fundamental mechanism of the objective occlusion effect induced by bone-conducted stimulation**. *JASA*.
- Doutres, O., Sgard, F., Terroir, J., Perrin, N., & Jolly, C. (2019). **A critical review of the literature on comfort of hearing protection devices: definition of comfort and identification of its main attributes for earplug types**. *International Journal of Audiology*.

要点：occlusion effect 的核心不是静态气压真的改变，而是耳道被部分/完全封闭后，耳道声阻抗、骨导声、耳道壁振动耦合改变，使低频自声和体传导声增强。半入耳如果为了降噪形成更强“半封闭感”，主观耳压和闷头会增加。

### 2. Open-ear / semi-open ANC 的物理限制

用途：解释为什么半入耳 ANC 在 1 kHz 以上更难稳定，佩戴差异、耳甲腔、泄漏路径会让耳膜处抵消误差变大。

建议补入：

- Yuan, K. et al. (2026). **Active noise cancellation on open-ear smart glasses**. arXiv:2604.05519. 该文明确把 open-ear ANC 的目标放在 100-1000 Hz，并指出开放耳设计不适配传统依赖耳道入口误差麦克风的 ANC 假设。
- Rivera Benois, P., Roden, R., Blau, M., & Doclo, S. (2021). **Sound Pressure Minimization at the Ear Drum for In-ear ANC Headphones using a Fixed Feedforward Remote Microphone Technique**. arXiv:2105.06894. 该文强调 reinsertions 和个体内差异会导致性能退化。
- Hilgemann, F., Chatzimoustafa, E., & Jax, P. (2025). **Data-Driven Uncertainty Modeling for Robust Feedback Active Noise Control in Headphones**. arXiv:2509.15864. 该文将不同佩戴状态建模为 feedback ANC 的不确定性来源。

要点：半入耳产品的 1-2 kHz 不足不一定只是算法没调深，也可能是开放路径、相位裕度、佩戴差异和稳健性共同限制。1 kHz 以上波长变短，耳膜目标点和 mic/driver 路径错配更敏感。

### 3. Speech intelligibility / presence 频带权重

用途：解释为什么 1-2 kHz 的残留比“500-1000 Hz 和 2-4 kHz 多 3 dB 降噪”更影响体验。

建议补入：

- ANSI S3.5 / Speech Intelligibility Index (SII) 相关资料。
- Articulation Index / Speech Interference Level 相关经典资料，尤其 500 Hz、1 kHz、2 kHz、4 kHz octave bands。
- French & Steinberg (1947). **Factors governing the intelligibility of speech sounds**. *JASA*.
- Kryter (1962). **Methods for the calculation and use of the Articulation Index**. *JASA*.

要点：1-3 kHz 是语音信息和存在感很高的区域。若 500-1000 Hz 与 2-4 kHz 被压得更深，但 1-2 kHz 相对残留，用户可能感知到一个“中频突起”：环境变暗了，但人声/机械中频残留更凸显，听感更顶、更近、更在头内。

### 4. 产品/开放式 ANC 公开资料

用途：作为设计合理性和竞品定位的旁证，不应当替代实测曲线。

建议补入：

- Apple AirPods 4 with ANC 的公开资料与第三方测试入口。公开报道将其描述为无耳塞/开放式设计下实现 ANC，且具备 Transparency / Adaptive Audio / Conversation Awareness。
- RTINGS 或同类测量平台的 AirPods 4 ANC noise isolation 页面，如能获取到曲线，应单独记录测量方法、固件版本、coupler/fixture、佩戴条件。

要点：AirPods 4 的设计价值可能不是“每段都更深”，而是在半开放结构下把残余谱做得更平滑，并用透明/自适应策略避免过强封闭感。

## 对当前问题的解释假设

你的现象可以形成下面这条证据链：

1. 半入耳缺少稳定密封，ANC 在 1 kHz 以上更受佩戴和泄漏路径影响。
2. 你们在 500-1000 Hz 和 2-4 kHz 比 AirPods 4 深约 3 dB，但 1-2 kHz 较弱。
3. 这可能造成 1-2 kHz 的相对残留峰，而不是自然连续的残余噪声谱。
4. 1-2 kHz 位于语音清晰度/存在感敏感区，残留峰会被放大感知。
5. 同时 500-1000 Hz 的强衰减会减少环境低中频包络，2-4 kHz 的强衰减会减少空气感/外化线索。
6. 结果是总能量下降，但主观听感变成“暗、闷、头内、中频残留突兀”，并被用户描述为耳压和闷头感。

## 建议加入现有矩阵的字段

- `fit_type`: sealed / vented / semi-in-ear / open-ear
- `occlusion_relevance`: none / indirect / direct
- `ear_canal_impedance`: discussed / not discussed
- `speech_band_relevance`: none / 500-4k / 1-3k / SII-STI
- `wearing_uncertainty`: insertion / reinsertion / leakage / concha geometry / head movement
- `residual_shape_claim`: smoother residual / spectral dip / spectral peak / masking / pleasantness

## 检索入口

- Occlusion effect 概念与参考文献列表：https://en.wikipedia.org/wiki/Occlusion_effect
- Yuan et al. 2026, open-ear ANC smart glasses：https://arxiv.org/abs/2604.05519
- Rivera Benois et al. 2021, eardrum pressure minimization for in-ear ANC：https://arxiv.org/abs/2105.06894
- Hilgemann et al. 2025, wearing uncertainty in feedback ANC headphones：https://arxiv.org/abs/2509.15864
- AirPods 4 with ANC 公开报道入口：https://www.theverge.com/2024/9/9/23313529/apple-airpods-4-noise-cancellation-price-features
- Open earbuds / AirPods 4 ANC 第三方评测入口：https://www.techradar.com/audio/earbuds-airpods/the-best-open-ear-headphones

## 结论

现有库偏“怎么做心理声学 ANC”，但对这个具体问题还需要补“为什么半入耳会耳压/闷、为什么 1-2 kHz 形状比两侧局部深度更关键”。优先补 open/vented fitting、occlusion effect、speech-band weighting、open-ear ANC robustness 四类资料。
