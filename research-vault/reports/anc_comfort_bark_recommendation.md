---
type: applied_synthesis
status: draft_for_listening_test
research_question: "ANC 舒适性：不同 Bark 增益以及 Bark 间关系如何影响降噪体验；不能改变耳机物理 PNC"
timestamp: 2026-06-17T00:00:00Z
evidence_policy: "每条工程建议都标注来源；数值曲线是基于文献原则的可测试假设，不是已被单篇论文直接验证的通用最优曲线。"
online_verification: "2026-06-26 使用 PubMed/NCBI E-utilities、ISCA Archive、公开 PDF、Salford 页面核验；Google Scholar 直连返回 403，未把 Scholar 页面作为可引用来源。"
---

# ANC 舒适降噪响度曲线与 Bark 频段约束（测试版）

## 0. 使用边界

- 你不能改变耳机外形，因此这里不建议调节物理 PNC；所有建议都限定在 DSP / ANC 目标函数 / 残余噪声整形 / 增益平滑 / 包络线控制。
- “舒适降噪响度曲线”不是简单最大降噪曲线。Priese 等指出，高降噪通常被假设会增加舒适性，但 ANC 研究常忽略舒适性的构成；听评显示 perceived loudness 不是唯一因素，pleasantness 也很重要。来源：The Need for Psychoacoustics in Active Noise Cancellation (2013)。
- Bao 和 Panahi 系列工作说明传统 ANC 最小化残余能量会忽略频域感知差异；应在 ANC 中加入 A-weighting、ITU-R 468 或类似 psychoacoustic weighting，并用 loudness、sharpness、roughness、tonality 等指标评估 residual sound quality。来源：Using A-weighting for psychoacoustic active noise control (2009)；Psychoacoustic Active Noise Control with ITU-R 468 Noise Weighting and its Sound Quality Analysis (2010)；A Perceptually Motivated Active Noise Control Design and Its Psychoacoustic Analysis (2013)。
- Cheong 等进一步说明，不只每个频段本身重要，频段之间的 spectral modulation / 谱形起伏也会影响感知；可以用 spectral-modulation-sensitive pre-emphasis 约束残余误差谱。来源：A Spectral Modulation Sensitivity Weighted Pre-emphasis Filter for Active Noise Control System (2016)。
- Rivera Benois 等在耳机原型上指出，耳机材料的被动衰减对 pleasantness 很关键；但在不能改 PNC 时，ANC 仍可进一步降低 loudness 和 roughness。来源：Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones (2018)。

### 0.1 使用边界中各方法的操作方式

> 证据说明：下面的操作方式只使用本 vault 中 `research-vault/literature/index.md` 已登记的文献作为依据。文献直接支持的是“为什么要用这些感知权重/指标/谱形约束”，具体阈值、窗口长度、阶梯幅度属于工程化落地参数，必须通过本机测量和听评校准。

> 在线数据库补充：2026-06-26 通过 NCBI E-utilities 核验 Bao & Panahi (2009, 2010) 的 PubMed 元数据与 abstract；通过 ISCA Archive 核验 Cheong et al. (2016) 条目；通过公开 PDF 核验 Priese et al. (2013) 与 Rivera Benois et al. (2018)；通过 University of Salford 页面核验 loudness / critical-band 说明。Google Scholar 查询页在当前环境返回 403 Forbidden，因此本报告不把 Scholar 检索页作为证据来源，只把可打开的线上数据库/出版方/公开 PDF 作为引用入口。

### 0.2 在线检索与数据库核验记录

| 来源 | 可核验入口 | 核验到的信息 | 用于本文的位置 |
|---|---|---|---|
| PubMed / NCBI E-utilities | PMID 19963645；DOI `10.1109/IEMBS.2009.5332654` | Bao & Panahi (2009) 题名、作者、页码 `5701-5704`、DOI、abstract。abstract 明确指出传统 ANC 用 SPL / residual error variance 会忽略人耳频率选择性，论文把 A-weighting 纳入 ANC，并用 loudness 评价。 | 方法 B：A-weighting psychoacoustic ANC；L1/M 分组的“不能只看能量最小化”。 |
| PubMed / NCBI E-utilities | PMID 21095758；DOI `10.1109/IEMBS.2010.5626197` | Bao & Panahi (2010) 题名、作者、页码 `4323-4326`、DOI、abstract。abstract 明确指出 ITU-R 468 反映人耳对随机噪声响应，并用 loudness、sharpness、roughness、tonality 组成 pleasantness model 评价 attenuation noise。 | 方法 C、D、H、I；H1/H2 的 sound-quality guardrail。 |
| ETRI / DOI | DOI `10.4218/etrij.13.0112.0822`；本地 vault 记录含出版方 URL 和 PDF URL | 本地记录显示 Bao & Panahi (2013) 指出传统 ANC 不区分频域听觉敏感性，并用 pleasantness model 结合 loudness、sharpness、roughness、tonality；记录还标注 ITU-R 468 可优于 A-weighting。 | 方法 D；舒适性不等于能量最小。 |
| ISCA Archive | `https://www.isca-archive.org/interspeech_2016/cheong16_interspeech.html` | ISCA 页面显示 Cheong, Wang & Chi (2016) 考虑 spectral 与 temporal modulation sensitivity；用 SPL 与 loudness level 评价；窄带/宽带噪声仿真和 TI C6713 DSP 验证；页面 DOI 为 `10.21437/Interspeech.2016-757`。 | 方法 E、F、G；Bark 间谱形起伏约束。 |
| 公开 PDF | Priese et al. (2013) `The Need for Psychoacoustics in Active Noise Cancellation` | PDF 明确说明高 noise reduction 常被假设提升 comfort，但听评显示 perceived loudness 不是唯一因素，pleasantness 也重要；还说明人耳在 2-5 kHz 最敏感，sharpness、roughness、tonality 会影响 pleasantness。 | 方法 D、H；M/H1 分组证据。 |
| 公开 PDF | Rivera Benois & Zölzer / Papantoni (2018) `Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones` | PDF 明确说明 psychoacoustic ANC 目标是降低 perceived loudness 和 annoyance，优先衰减人耳敏感频率；PNC 对 pleasantness 关键，低频由 ANC 主动处理；hybrid 结构结合 psychoacoustic feedforward 与低频 feedback，实测中 ANC 可进一步降低 loudness/roughness。 | 方法 A、J；L0/L1 低频 ANC 与 headphone 证据。 |
| University of Salford | `Loudness and critical bands` 页面 | 页面说明 loudness 依赖频率内容；20 Hz 40 dB 比 1 kHz 40 dB 听起来更小；复杂声 loudness 需要 critical bandwidth；小于一个 critical bandwidth 的双音会部分 masking；specific loudness 可按 sone/Bark 表达并积分。 | Bark 分组、specific loudness、critical-band / masking 依据。 |
| Google Scholar | `https://scholar.google.com/scholar?q=...` | 当前环境命令行访问返回 Google 403 Forbidden，因此未获得可核验 Scholar 结果。 | 不作为证据来源；后续可由人工在浏览器登录环境中补录 Scholar citation / related articles。 |

#### 方法 A：DSP-only ANC target，不改物理 PNC

- **适用边界**：耳机外形、耳塞/导管、开孔、材料、麦克风/扬声器位置不能改，只允许改变 ANC 控制目标、滤波器权重、目标增益、平滑和保护逻辑。
- **操作步骤**：
  1. 固定同一只样机、同一佩戴方式、同一噪声回放链路，分别记录 ANC off、当前 ANC、候选 ANC 的耳道或 HATS 测量。
  2. 将测得的残余声按 1/3 octave 或 Bark 频带汇总，至少输出 `residual SPL`、`ANC insertion loss`、`specific loudness 或等效 loudness proxy`。
  3. 所有候选曲线只改 DSP target，不改 PNC；每次改动后重新记录实测曲线，避免把佩戴差异误判为算法差异。
  4. 人因听评只比较同一物理结构下的不同 target：舒适、耳压、闷头、自然度、突兀感、总体偏好。
- **判据**：若某候选 target 的总 loudness 下降，但 sharpness、roughness、tonality 或主观耳压显著恶化，不进入默认曲线。
- **文献依据**：Rivera Benois et al. (2018) 记录显示 PNC 对 pleasantness 很关键，但在给定耳机结构下，ANC 仍可进一步降低 loudness 和 roughness；Priese et al. (2013) 说明高降噪不等于舒适，pleasantness 需要单独评价。

#### 方法 B：A-weighting psychoacoustic ANC

- **用途**：把传统“最小化残余声能量”的目标改成“优先处理人耳更敏感的频段”。
- **操作步骤**：
  1. 对误差信号或频带残余声计算 A-weighted error：`E_A[f] = A[f] * E[f]`。
  2. 若系统是自适应滤波结构，将 A-weighted error 用于更新或离线求解目标滤波器；若系统只支持 target table，则把 A-weighting 转成频带权重表。
  3. 生成一条 A-weighting 候选曲线，与未加权能量最小化曲线做同场景对照。
  4. 输出客观指标：总 SPL、A-weighted SPL、Bark-band residual、loudness proxy。
  5. 用听评验证：A-weighting 是否降低“听起来吵”的程度，同时不引入 2-5 kHz 的尖锐或压迫感。
- **注意**：A-weighting 是粗粒度听感权重，不等同于舒适模型；不能只凭 A-weighted SPL 选择最终曲线。
- **文献依据**：Bao & Panahi (2009) 在 psychoacoustic ANC 中引入 A-weighting，使残余噪声控制比未加权能量最小化更贴近人耳敏感性。

#### 方法 C：ITU-R 468 或类似噪声权重 ANC

- **用途**：与 A-weighting 做对照，评估更强调音频噪声可感知性的权重是否更适合 ANC residual。
- **操作步骤**：
  1. 将残余误差信号通过 ITU-R 468 weighting 或将其离散成频带权重。
  2. 生成 `ITU-R 468 target`，与 `unweighted target`、`A-weighting target` 同时测量。
  3. 对每个 target 计算 loudness、sharpness、roughness、tonality 或对应 proxy。
  4. 若 ITU-R 468 让总残余声变小但 sharpness/tonality 上升，降低 2.7 kHz 以上的权重或加入 high-Bark guardrail。
  5. 用主观听评比较“安静感”和“烦躁/尖锐/压迫感”是否分离。
- **判据**：不以单个加权 dB 指标作为最终选择，而以“加权指标改善 + 声质量指标不恶化 + 主观舒适提升”为通过条件。
- **文献依据**：Bao & Panahi (2010) 将 ITU-R 468 weighting 用于 psychoacoustic ANC，并用 loudness、roughness、sharpness、tonality 评价残余声质量；Bao & Panahi (2013) 的摘要记录指出 ITU-R 468 可优于 A-weighting。

#### 方法 D：Perceptual weighting / pleasantness model

- **用途**：把“安静”与“舒适”拆开，避免只追求残余声能量最低。
- **操作步骤**：
  1. 对每条候选曲线计算至少四类客观指标：loudness、sharpness、roughness、tonality。
  2. 形成候选评分表：`overall_score = loudness_term + sharpness_penalty + roughness_penalty + tonality_penalty`。权重先设为听评前的工程假设。
  3. 每条曲线进入听评，采集舒适、压迫感、自然度、突兀感和总体偏好。
  4. 用听评结果回归或排序校准每个 penalty 的权重；不在没有听评的情况下固定“最优权重”。
  5. 将通过的 target 固化为场景化曲线，而不是单一全场景默认曲线。
- **判据**：若 loudness 降低但 pleasantness 或总体偏好下降，该 target 只作为强降噪模式，不作为舒适默认曲线。
- **文献依据**：Bao & Panahi (2013) 指出传统 ANC 忽略频域感知差异，并用 pleasantness model 结合 loudness、sharpness、roughness、tonality 评价残余噪声；Priese et al. (2013) 指出 perceived loudness 不是舒适性的唯一因素。

#### 方法 E：Residual noise shaping

- **用途**：在能力受限的频点压不下去时，调整相邻频带的残余谱形，让残余声更连续、更少突兀。
- **操作步骤**：
  1. 先固定不可控区域，例如 1 kHz 附近因能力限制不能继续加深。
  2. 生成只改相邻频带的阶梯 target，例如：`500-1000 Hz 回退`、`2-4 kHz 回退`、`两侧同时回退`、`两侧平滑过渡`。
  3. 对每条 target 计算 `局部残余峰值 = target中心频带残余 - 两侧残余均值`。
  4. 听评中单独问“中频突兀/顶/头内感”，验证相对残余峰是否比总降噪量更能解释不适。
  5. 选择“总降噪可接受 + 局部残余峰较小 + 舒适偏好更高”的目标谱形。
- **判据**：如果加深两侧使中心不可控频点更凸显，应回退两侧或改用平滑过渡，即使宽频平均降噪变浅。
- **文献依据**：Cheong et al. (2016) 将 spectral modulation sensitivity 引入 ANC，支持不只看每个频点本身，还要考虑谱形起伏；Salford (2024) 说明复杂声响度与 critical bands、频带内 masking / summation 有关。

#### 方法 F：Bark 增益平滑 / spectral modulation penalty

- **用途**：避免相邻 Bark 之间出现锯齿、窄凹、窄峰，降低残余声染色和中频突兀。
- **操作步骤**：
  1. 把 target 写成 Bark-band gain：`G[z]`。
  2. 计算一阶差分 `D1[z] = G[z] - G[z-1]`，表示相邻 Bark 的斜率。
  3. 计算二阶差分 `D2[z] = G[z+1] - 2G[z] + G[z-1]`，表示局部弯折/峰谷。
  4. 在目标函数中加入 `λ2 * Σ D1[z]^2 + λ3 * Σ D2[z]^2`；若系统不支持目标函数，则离线生成 target table 后做 Bark 维度平滑。
  5. 对 1 kHz 附近无法加深的场景，重点控制 `500 Hz-4 kHz` 的局部峰谷，而不是只追求两侧更深。
- **判据**：斜率阈值和 3-Bark 峰谷阈值是工程初值，必须通过听评校准；文献只支持“谱形起伏影响感知”，不直接给出本产品阈值。
- **文献依据**：Cheong et al. (2016) 用 spectral-modulation-sensitive pre-emphasis shaping residual error，并用 SPL 和 loudness level 评价，摘要记录显示其在仿真和 DSP 硬件验证中优于对照系统。

#### 方法 G：包络线 / attack-release 控制

- **用途**：避免低频 ANC 深度快速变化导致 pumping、抽吸感或耳压感。
- **操作步骤**：
  1. 对每个场景的 target gain 加时间平滑：`G_smooth[t,z] = smooth(G_raw[t,z])`。
  2. 将 attack 和 release 分开设置：突发噪声不立即追到最大深度，噪声消失后也不瞬间释放。
  3. 低频 Bark 0-3 使用更慢的变化率；中高频只允许小幅、平滑变化。
  4. 每条候选 target 记录动态场景下的 gain trace，而不只记录稳态频响。
  5. 听评中加入“压迫感、抽吸感、变化是否被察觉”的动态题项。
- **判据**：当前 vault 没有直接给出 ANC attack/release 数值的文献；因此报告中的 200-500 ms、500-1500 ms 只能作为工程起点，需要动态听评确认。
- **文献依据**：Cheong et al. (2016) 的直接证据是 spectral modulation / residual shaping，不是 attack-release 数值；此方法在本文中属于由“谱形/调制感知重要”推导的工程假设。

#### 方法 H：Sharpness guardrail

- **用途**：防止“总 loudness 下降，但 2-5 kHz 更刺、更烦”。
- **操作步骤**：
  1. 对每条候选曲线计算 sharpness 或 high-Bark energy proxy。
  2. 若 `Bark 15-19` 或约 `2.7-5.3 kHz` 出现正增益、泄漏补偿放大或残余尖峰，优先回退。
  3. 对用户主观题设置“尖锐、刺耳、压迫、疲劳”维度。
  4. 通过条件是：总 loudness 降低时，sharpness 不上升，且主观尖锐/疲劳不恶化。
- **判据**：Bark 15 以上原则上不把“更深降噪”作为第一目标，先避免放大和尖锐感。
- **文献依据**：Priese et al. (2013) 记录人耳在约 2-5 kHz 敏感，且高降噪不等于舒适；Bao & Panahi (2010, 2013) 将 sharpness 纳入残余声质量/pleasantness 评价；Rivera Benois et al. (2018) 也使用 loudness、roughness、sharpness 等 psychoacoustic 指标。

#### 方法 I：Tonal peak / whistle detector

- **用途**：避免窄带峰导致 whistle、机械音、电子伪影或局部 annoyances。
- **操作步骤**：
  1. 在 Bark 汇总之外保留窄带 FFT 或 1/12 octave 检测，避免窄峰被 Bark 平均掩盖。
  2. 对每条候选曲线计算 `peak prominence = 窄带峰值 - 邻域均值`。
  3. 若窄峰突出，优先使用窄带 notch、局部误差权重提升或 target 局部回退；不要整段 Bark 大幅加深。
  4. 听评中加入“啸叫、单音、电子音、机械感”题项。
  5. 通过条件是 tonal peak 下降且不牺牲整体自然度。
- **判据**：报告中 `>6 dB` 这类峰值阈值是工程起点；当前 vault 只支持 tonality 是声质量维度，不直接给出本产品阈值。
- **文献依据**：Bao & Panahi (2010, 2013) 将 tonality 纳入 residual sound quality / pleasantness 评价。

#### 方法 J：场景化 target

- **用途**：避免用同一条曲线同时服务通勤、办公室、人声、安静环境，导致某些场景舒适性崩溃。
- **操作步骤**：
  1. 建立场景标签：交通/飞机低频、办公室人声、空调/风扇宽带、安静环境。
  2. 每个场景分别测 ANC off 噪声谱和当前 ANC residual。
  3. 针对每个场景生成 3-4 条候选 target：最大能量降噪、A-weighting、ITU-R 468、Bark 平滑舒适曲线。
  4. 每个场景单独听评，不把通勤最佳曲线直接用于办公室默认曲线。
  5. 最终输出“默认舒适曲线 + 强降噪曲线 + 办公/人声保守曲线”的模式集合。
- **判据**：场景化 target 的选择必须同时看客观指标和用户主观偏好。
- **文献依据**：Priese et al. (2013) 支持舒适性不只由 perceived loudness 决定；Bao & Panahi (2009, 2010, 2013) 支持按感知权重和 sound quality 指标评价 ANC residual；Rivera Benois et al. (2018) 支持 headphone 场景中 psychoacoustic ANC 的必要性。

## 1. Bark 频段分组

| 组 | Bark | 近似频段 | ANC/舒适性含义 | 证据属性 |
|---|---:|---|---|---|
| L0 | 0-3 | 20-300 Hz | 压力感、轰鸣、交通/空调低频；ANC 最有效区；过深或快速变化可能产生“耳压/抽吸感” | 文献支持 + 工程假设 |
| L1 | 3-7 | 300-920 Hz | 低中频浑浊、舱噪主体；适合较强但平滑降噪 | 文献支持 + 工程假设 |
| M | 7-15 | 920 Hz-2.7 kHz | 语音/提示音/环境可感知性；过度不均匀衰减会让残余噪声显得空洞或突兀 | 文献支持 + 工程假设 |
| H1 | 15-19 | 2.7-5.3 kHz | 人耳敏感区；同等 SPL 更显著，sharpness/annoyance 风险高；不建议由 ANC 算法放大 | 文献支持 |
| H2 | 19-24 | 5.3-15.5 kHz | 多由 PNC 决定；ANC 可控性弱；避免 hiss、尖锐感和高频补偿放大 | 文献支持 + 工程假设 |

### 1.1 Bark 分组的文献引用与对应结论

> 证据说明：当前 vault 中没有任何一篇文献直接验证本文 L0/L1/M/H1/H2 这套产品分组是“最优分组”。分组来自 Bark / critical-band 组织方式、ANC 低频优势、psychoacoustic ANC、sound-quality 指标和 headphone ANC 的组合推导。下表逐项列出直接文献结论与本文使用方式，避免把工程假设包装成文献结论。

| 分组 | 文献引用 | 数据库记录的文献结论 | 对本分组的支持方式 | 结论边界 |
|---|---|---|---|---|
| L0：Bark 0-3，20-300 Hz | Salford (2024) `Loudness and critical bands` | equal-loudness contours 显示，低频要达到与 1 kHz 相同响度需要更高声功率；复杂声 loudness 需要按 critical bandwidth 处理，频带内存在 masking / summation。 | 支持用 Bark/critical-band 而不是线性频率或单一 dB(A) 来组织低频 loudness；支持低频与 1 kHz 的感知敏感性不同。 | 不直接证明 L0 应设为 20-300 Hz，也不直接证明“耳压/抽吸感”阈值；这些是产品工程假设，需要听评。 |
| L0：Bark 0-3，20-300 Hz | Rivera Benois et al. (2018) `Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones` | headphone hybrid ANC 中，psychoacoustic feedforward control 与 feedback low-frequency attenuation 结合；被动衰减主导 pleasantness，但 ANC 仍可降低 loudness 和 roughness。 | 支持低频 feedback/ANC 是 headphone ANC 的重要控制区，并支持即使 PNC 固定，ANC 仍可改善 loudness/roughness。 | 文献不直接给出“低频目标应为 -8 到 -12 dB”或本产品默认曲线。 |
| L1：Bark 3-7，300-920 Hz | Bao & Panahi (2009) `Using A-weighting for psychoacoustic active noise control` | 将 A-weighting 引入 adaptive ANC，使 residual noise control 比未加权能量最小化更符合人耳频率敏感性。 | 支持 L1 不应只按能量最小化，而应按频率敏感性加权处理；低中频可以作为主降噪区但需要与感知权重结合。 | A-weighting 不是 Bark 分组文献，也不直接给 L1 的目标深度。 |
| L1：Bark 3-7，300-920 Hz | Salford (2024) | critical-band loudness 比单独 dB(A) 更有感知意义；频带内 masking / summation 会影响复杂声 loudness。 | 支持将 300-920 Hz 作为相邻 Bark 组平滑处理，避免只看窄点 SPL。 | 不直接证明“舱噪主体”或“适合较强但平滑降噪”；这些需要结合实际噪声谱。 |
| M：Bark 7-15，920 Hz-2.7 kHz | Priese et al. (2013) `The Need for Psychoacoustics in Active Noise Cancellation` | 高 noise reduction 不足以说明 ANC headphone comfort；听评显示 perceived loudness 不是唯一因素，pleasantness 很重要；记录强调约 2-5 kHz 人耳敏感性。 | 支持中频/高中频不能只追求更深降噪，需要同时看 pleasantness 和敏感频段。 | 文献强调 2-5 kHz，并不直接覆盖整个 920 Hz-2.7 kHz；M 组的“语音/环境可解释性”需要额外语音文献补强，当前 vault 未收录。 |
| M：Bark 7-15，920 Hz-2.7 kHz | Cheong et al. (2016) `A Spectral Modulation Sensitivity Weighted Pre-emphasis Filter for Active Noise Control System` | 在频率敏感阈值之外加入 spectral modulation sensitivity；pre-emphasis filter 用于 shaping residual error，并以 SPL 与 loudness level 评价。 | 支持 M 组内部及相邻组之间的谱形起伏会影响感知；支持不要让 1 kHz 附近因两侧过深而形成相对残余峰。 | 文献不直接研究 AirPods 或半入耳 1 kHz 问题；本文将其用于解释“谱形起伏”是合理外推。 |
| H1：Bark 15-19，2.7-5.3 kHz | Priese et al. (2013) | 记录强调 2-5 kHz 的人耳敏感性，并指出舒适性不能只由 perceived loudness 决定。 | 直接支持把 2.7-5.3 kHz 作为高敏感风险区；支持 H1 不宜做高频补偿放大或激进 ANC。 | 不直接给出 H1 的禁止正增益阈值；`G <= 0 dB` 是工程 guardrail。 |
| H1：Bark 15-19，2.7-5.3 kHz | Bao & Panahi (2010)；Bao & Panahi (2013) | 2010 工作用 ITU-R 468 weighting，并用 loudness、roughness、sharpness、tonality 评价 residual sound quality；2013 工作用 pleasantness model 结合 loudness、sharpness、roughness、tonality。 | 支持 H1 需要 sharpness/tonality guardrail，而不是只看总 SPL 或宽频降噪量。 | 文献支持指标框架，不直接给出 H1 的目标 dB。 |
| H2：Bark 19-24，5.3-15.5 kHz | Bao & Panahi (2010, 2013) | residual sound quality 需要 loudness、sharpness、roughness、tonality / pleasantness 综合评价。 | 支持高频若出现 hiss、tonal peak、sharpness 上升，即使总 loudness 下降也不应接受。 | 当前 vault 没有直接证明 H2 “多由 PNC 决定”或 ANC 高频可控性弱；这是 ANC 工程常识，本文应标为工程假设。 |
| H2：Bark 19-24，5.3-15.5 kHz | Rivera Benois et al. (2018) | headphone 中 passive attenuation 对 pleasantness 很关键，ANC 仍可降低 loudness 和 roughness。 | 间接支持高频 comfort 不能只靠 ANC target，物理衰减会强烈影响 pleasantness；在 PNC 固定时，高频 DSP 更应保守。 | 文献不直接给出 5.3-15.5 kHz 的 target 或 hiss 阈值。 |
| 全频分组 / Bark 方法 | Salford (2024)；Cheong et al. (2016) | Salford 支持 critical-band loudness / masking / summation；Cheong 支持 spectral modulation sensitivity 与 residual shaping。 | 支持本文以 Bark 为频带索引，并对 Bark 间关系加平滑/峰谷约束。 | Bark 分组是组织框架，不代表每个产品都应使用相同边界；需要按实测听评校准。 |

## 2. 建议的“舒适降噪响度曲线”（以 residual loudness reduction / Bark 为目标）

下面数值是**初始可听评调参目标**：它把每个 Bark 上希望降低的 specific loudness 或等效 Bark-band level 转成相对目标，而不是声学硬指标。需要用真实耳机、真实噪声和用户听评校准。

| Bark | 近似频率 | 建议目标：相对 residual loudness 降低 | 约束 |
|---:|---|---:|---|
| 0 | 20-100 Hz | -6 到 -9 dB 等效 | 不追求瞬时极深；避免低频泵动 |
| 1 | 100-200 Hz | -8 到 -12 dB 等效 | 主降噪区，时间平滑优先 |
| 2 | 200-300 Hz | -8 到 -12 dB 等效 | 与 Bark 1/3 斜率连续 |
| 3 | 300-400 Hz | -7 到 -11 dB 等效 | 保持与中频自然过渡 |
| 4-6 | 400-770 Hz | -6 到 -10 dB 等效 | 舱噪/空调可明显降低，但避免过窄凹口 |
| 7-10 | 770 Hz-1.5 kHz | -4 到 -8 dB 等效 | 保留环境可解释性，减少“真空感” |
| 11-14 | 1.5-2.7 kHz | -3 到 -6 dB 等效 | 不要造成语音残片突兀；重点控制 tonal peaks |
| 15-18 | 2.7-4.4 kHz | -2 到 -5 dB 等效；禁止正增益 | 人耳敏感区，若 ANC 无法稳定衰减，至少避免放大 |
| 19-21 | 4.4-7.7 kHz | 0 到 -3 dB 等效；禁止 hiss | 更多依赖 PNC；DSP 只做尖锐度/嘶声风险控制 |
| 22-24 | 7.7-15.5 kHz | 0 dB 或轻微衰减 | 不建议 ANC 主动追高频深降噪 |

### 推荐曲线形状

```text
目标降噪深度
12 dB |        _______
10 dB |      _/       \_
 8 dB |  ___/           \___
 6 dB |_/                   \__
 4 dB |                       \___
 2 dB |                           \__
 0 dB +---+---+---+---+---+---+---+---
       B0  B3  B6  B9 B12 B15 B18 B24
```

解释：主峰放在 1-6 Bark（约 100-770 Hz），7-14 Bark 渐降，15 Bark 以上以“避免放大/避免尖锐/避免 hiss”为主，而不是追求最大 ANC。

## 3. Bark 间关系约束

| 约束 | 建议阈值 | 目的 | 来源/依据 |
|---|---:|---|---|
| 相邻 Bark 目标增益斜率 | `|G[z]-G[z-1]| <= 2 dB/Bark`，低频可放宽到 3 dB/Bark | 避免谱形锯齿、残余声染色、局部突兀 | Cheong 2016 的 spectral modulation 思路；critical-band loudness summation |
| 3-Bark 局部峰谷 | 任意 3 Bark 内峰谷差 `< 5 dB` | 降低 narrow spectral ripple 的可感知性 | Cheong 2016；Salford critical-band masking 说明 |
| 高频放大限制 | Bark 15 以上 `G <= 0 dB`，最好 `< -1 dB` 或旁路 | 避免 2-5 kHz 敏感区 sharpness/annoyance 增加 | Priese 2013；Bao/Panahi 2013；Rivera Benois 2018 |
| 低频泵动限制 | Bark 0-3 的目标增益变化速率 `< 1 dB / 100 ms` | 避免耳压感和抽吸感 | 工程假设，需听评验证 |
| 总 loudness 单调性 | 总 loudness 下降时，sharpness、roughness 不得显著上升 | 防止“更小声但更烦” | Bao/Panahi 2010/2013；Rivera Benois 2018 |
| Tonal peak 保护 | 任何 Bark 内窄带峰值若突出邻域 `> 6 dB`，优先压峰而不是全带加深 | 减少 whistle / tonal annoyance | Bao/Panahi 2010/2013 的 tonality 指标 |

## 4. 除 Bark 增益外还能调什么

1. **包络线 / attack-release**  
   - 低频 ANC 深度不要快速跳变；建议 attack 200-500 ms、release 500-1500 ms 起步听评。  
   - 对突发噪声不要瞬间追踪到最大降噪，否则容易产生 pumping 或“压迫感”。  
   - 证据状态：工程假设；Cheong 2016 说明 temporal modulation 对听觉重要，但其实时 ANC 中直接建模 temporal modulation 不实用，因此可先用包络线约束替代。

2. **谱形平滑 / spectral modulation penalty**  
   - 在控制目标中加入 `lambda_s * ||D_z G||` 或 `lambda_s * ||D_zz G||`，惩罚 Bark 维度的一阶/二阶起伏。  
   - 目标不是让每个 Bark 最大衰减，而是让 residual specific loudness 谱更平滑、更少尖峰。  
   - 证据状态：Cheong 2016 支持 spectral modulation sensitivity 影响 ANC 感知性能。

3. **Sharpness guardrail**  
   - 若总 loudness 降低但 sharpness 上升，则回退 2.7 kHz 以上的任何补偿或泄漏放大。  
   - 证据状态：Bao/Panahi 2013、Rivera Benois 2018 使用 loudness/sharpness/roughness/tonality/pleasantness 评价残余声。

4. **Tonal peak / whistle detector**  
   - 对窄带尖峰单独做 notch 或权重提升，而不是整段 Bark 大幅增强 ANC。  
   - 证据状态：Bao/Panahi 2010/2013 把 tonality 纳入 sound quality / pleasantness。

5. **场景化 target**  
   - 通勤/飞机：加深 Bark 0-7。  
   - 办公/人声环境：Bark 7-15 保守，避免语音残片被处理得不自然。  
   - 安静环境：整体减小 ANC 深度，优先低 hiss、低 roughness。

## 5. 可直接实现的目标函数草案

令 `N_res[z]` 为残余 specific loudness，`N_ref[z]` 为 ANC off 或上一稳定状态 specific loudness，`G[z]` 为 Bark 目标降噪量。

```text
minimize:
  Σ_z w_loud[z] * N_res[z]
+ λ1 * Σ_z max(0, G[z] - G_max[z])^2
+ λ2 * Σ_z (G[z] - G[z-1])^2
+ λ3 * Σ_z (G[z+1] - 2G[z] + G[z-1])^2
+ λ4 * sharpness_guard
+ λ5 * roughness_or_envelope_penalty
+ λ6 * tonal_peak_penalty
```

初始权重建议：

| 项 | 建议 |
|---|---|
| `w_loud[z]` | 1-6 Bark 高；15-19 Bark 设为“禁止放大”而非强降噪；19-24 Bark 很低 |
| `λ2, λ3` | 中高，确保 Bark 间连续 |
| `λ4` | 高，sharpness 上升立即回退 |
| `λ5` | 中高，低频包络变化更严格 |
| `λ6` | 中，发现 tonal peak 时局部提升 |

## 6. 下一步听评实验

- 固定耳机结构与 PNC，采集 3 类噪声：交通/飞机低频、办公室人声/键盘、空调/风扇宽带。
- 对每类噪声生成 4 组 ANC target：最大能量降噪、A-weighting、ITU-R 468、本文 Bark 平滑舒适曲线。
- 每组记录 loudness、specific loudness over Bark、sharpness、roughness、tonality，以及用户主观评分：舒适、压迫感、自然度、可忍受时长、疲劳。
- 只把“总 loudness 下降且 sharpness/roughness/tonality 不恶化、主观舒适评分提升”的曲线纳入默认 target。

## 7. 可引用文献列表

- Bao, H., & Panahi, I. M. S. (2009). Using A-weighting for psychoacoustic active noise control. DOI: 10.1109/IEMBS.2009.5332654.
- Bao, H., & Panahi, I. M. S. (2010). Psychoacoustic Active Noise Control with ITU-R 468 Noise Weighting and its Sound Quality Analysis. DOI: 10.1109/IEMBS.2010.5626197.
- Bao, H., & Panahi, I. M. S. (2013). A Perceptually Motivated Active Noise Control Design and Its Psychoacoustic Analysis. DOI: 10.4218/etrij.13.0112.0822.
- Priese, S., Bruhnken, C., Voss, D., & Reithmeier, E. (2013). The Need for Psychoacoustics in Active Noise Cancellation.
- Cheong, K.-M., Wang, Y.-Y., & Chi, T.-S. (2016). A Spectral Modulation Sensitivity Weighted Pre-emphasis Filter for Active Noise Control System. DOI: 10.21437/Interspeech.2016-757.
- Rivera Benois, P., Papantoni, V., & Zölzer, U. (2018). Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones.
- Acoustics Innovation Institute, University of Salford. Loudness and critical bands.
