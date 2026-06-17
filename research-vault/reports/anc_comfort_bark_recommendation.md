---
type: applied_synthesis
status: draft_for_listening_test
research_question: "ANC 舒适性：不同 Bark 增益以及 Bark 间关系如何影响降噪体验；不能改变耳机物理 PNC"
timestamp: 2026-06-17T00:00:00Z
evidence_policy: "每条工程建议都标注来源；数值曲线是基于文献原则的可测试假设，不是已被单篇论文直接验证的通用最优曲线。"
---

# ANC 舒适降噪响度曲线与 Bark 频段约束（测试版）

## 0. 使用边界

- 你不能改变耳机外形，因此这里不建议调节物理 PNC；所有建议都限定在 DSP / ANC 目标函数 / 残余噪声整形 / 增益平滑 / 包络线控制。
- “舒适降噪响度曲线”不是简单最大降噪曲线。Priese 等指出，高降噪通常被假设会增加舒适性，但 ANC 研究常忽略舒适性的构成；听评显示 perceived loudness 不是唯一因素，pleasantness 也很重要。来源：The Need for Psychoacoustics in Active Noise Cancellation (2013)。
- Bao 和 Panahi 系列工作说明传统 ANC 最小化残余能量会忽略频域感知差异；应在 ANC 中加入 A-weighting、ITU-R 468 或类似 psychoacoustic weighting，并用 loudness、sharpness、roughness、tonality 等指标评估 residual sound quality。来源：Using A-weighting for psychoacoustic active noise control (2009)；Psychoacoustic Active Noise Control with ITU-R 468 Noise Weighting and its Sound Quality Analysis (2010)；A Perceptually Motivated Active Noise Control Design and Its Psychoacoustic Analysis (2013)。
- Cheong 等进一步说明，不只每个频段本身重要，频段之间的 spectral modulation / 谱形起伏也会影响感知；可以用 spectral-modulation-sensitive pre-emphasis 约束残余误差谱。来源：A Spectral Modulation Sensitivity Weighted Pre-emphasis Filter for Active Noise Control System (2016)。
- Rivera Benois 等在耳机原型上指出，耳机材料的被动衰减对 pleasantness 很关键；但在不能改 PNC 时，ANC 仍可进一步降低 loudness 和 roughness。来源：Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones (2018)。

## 1. Bark 频段分组

| 组 | Bark | 近似频段 | ANC/舒适性含义 | 证据属性 |
|---|---:|---|---|---|
| L0 | 0-3 | 20-300 Hz | 压力感、轰鸣、交通/空调低频；ANC 最有效区；过深或快速变化可能产生“耳压/抽吸感” | 文献支持 + 工程假设 |
| L1 | 3-7 | 300-920 Hz | 低中频浑浊、舱噪主体；适合较强但平滑降噪 | 文献支持 + 工程假设 |
| M | 7-15 | 920 Hz-2.7 kHz | 语音/提示音/环境可感知性；过度不均匀衰减会让残余噪声显得空洞或突兀 | 文献支持 + 工程假设 |
| H1 | 15-19 | 2.7-5.3 kHz | 人耳敏感区；同等 SPL 更显著，sharpness/annoyance 风险高；不建议由 ANC 算法放大 | 文献支持 |
| H2 | 19-24 | 5.3-15.5 kHz | 多由 PNC 决定；ANC 可控性弱；避免 hiss、尖锐感和高频补偿放大 | 文献支持 + 工程假设 |

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
- Cheong, K.-M., Wang, Y.-Y., & Chi, T.-S. (2016). A Spectral Modulation Sensitivity Weighted Pre-emphasis Filter for Active Noise Control System. DOI: 10.21437/Interspeech.2016-1315.
- Rivera Benois, P., Papantoni, V., & Zölzer, U. (2018). Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones.
- Acoustics Innovation Institute, University of Salford. Loudness and critical bands.
