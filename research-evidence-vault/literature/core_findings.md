# Core Findings

|paper|year|finding|
|---|---|---|
|Using A-weighting for psychoacoustic active noise control|2009|Incorporates A-weighting into adaptive active noise cancellation from a psychoacoustic point of view so residual noise control better reflects human hearing sensitivity than unweig|
|Psychoacoustic Active Noise Control with ITU-R 468 Noise Weighting and its Sound Quality Analysis|2010|Applies ITU-R 468 noise weighting to psychoacoustic ANC and evaluates residual noise sound quality using a comfort model with loudness, roughness, sharpness, and tonality; related |
|A Perceptually Motivated Active Noise Control Design and Its Psychoacoustic Analysis|2013|Traditional ANC minimizes residual noise energy without frequency discrimination, but human hearing has selective frequency sensitivity. The paper incorporates noise weighting into|
|The Need for Psychoacoustics in Active Noise Cancellation|2013|Argues that high noise reduction alone is insufficient for ANC headphone comfort; test-person evaluation indicates perceived loudness is not the only factor and pleasantness is imp|
|A Spectral Modulation Sensitivity Weighted Pre-emphasis Filter for Active Noise Control System|2016|Extends psychoacoustic ANC beyond frequency-dependent hearing thresholds by considering spectral modulation sensitivity. The proposed pre-emphasis filter shapes residual error and |
|Psychoacoustic Hybrid Active Noise Control Structure for Application in Headphones|2018|Psychoacoustic ANC aims to reduce perceived loudness and annoyance by prioritizing frequencies where human hearing is more sensitive. A hybrid headphone structure combines psychoac|
|Loudness and critical bands|2024|Explains that equal-loudness contours show low-frequency tones need more sound power to be as loud as 1 kHz, and complex sound loudness requires critical bandwidths because tones w|
|Active Noise Control: A Tutorial Review|1999|Foundational ANC review; establishes ANC effectiveness mainly at low frequencies and practical constraints important when PNC geometry cannot be changed.|
|Active noise control|1993|Review of active noise control principles and implementation limits; useful baseline for separating physical cancellation limits from perceptual target shaping.|
|Recent advances on active noise control: open issues and innovative applications|2012|Review article summarizing ANC algorithms, applications, constraints, and open issues; reinforces that passive methods are less effective at low frequencies and ANC is practical ma|
|Active Noise Control Systems: Algorithms and DSP Implementations|1996|Core ANC algorithms and DSP implementation reference; supports algorithmic rather than physical PNC changes.|
|Psychoacoustics: Facts and Models|2007|Foundational psychoacoustics reference for Bark scale, critical bands, masking, loudness, sharpness, and roughness.|
|Incorporation of loudness measures in active noise control|2001|Uses loudness measures within ANC evaluation/control rather than relying only on squared pressure.|
|Residual Noise Shaping Technique for Active Noise Control Systems|1994|Early residual-noise shaping paper; relevant to comfort curves because it changes residual spectrum rather than only minimizing total energy.|
|Development and experiment of narrowband active noise equalizer|1993|Active noise equalizer reference cited in active sound-quality-control reviews; relevant to controlled residual spectrum.|
|Broadband Adaptive Noise Equalizer|1996|Adaptive noise equalizer for broadband residual sound shaping; related to user-preferred residual spectra.|
|Development and analysis of an adaptive noise equalizer|1995|Adaptive noise equalizer reference; supports designing residual spectrum rather than only maximizing attenuation.|
|Frequency-Domain Periodic Active Noise Control and Equalization|1997|Frequency-domain periodic ANC and equalization; relevant to tonal/periodic components and residual shaping.|
|Adaptive noise equalizer with equal-loudness compensation|2005|Uses equal-loudness compensation in an adaptive noise equalizer, directly related to perceptual weighting.|
|Multichannel active noise control system for local spectral reshaping of multifrequency noise|2004|Multichannel ANC for local spectral reshaping; relevant to Bark-band and tonal residual control.|
|Development of adaptive algorithm for active sound quality control|2007|Active sound quality control algorithm; supports optimizing perceived quality rather than SPL alone.|
|Frequency-domain delayless active sound quality control algorithm|2008|Delayless frequency-domain ASQC; relevant to real-time headphone implementation constraints.|
|Sound quality of low-frequency and car engine noises after active noise control|2003|Shows ANC changes sound quality dimensions for low-frequency and engine noise, so loudness reduction alone is insufficient.|
|Sound quality evaluation for the vehicle HVAC system after active noise control|2008|HVAC ANC sound-quality evaluation; relevant to comfort under fan/air-conditioning noise.|
|Review and future perspectives on Active Sound Quality Control|2010|Review argues mere noise reduction by ANC does not guarantee sound-quality improvement; cites loudness measures and active equalization.|
|Review of active noise control techniques with emphasis on sound quality enhancement|2018|Review focused on ANC development for sound-quality enhancement and residual spectrum requirements.|
|Integrated psychoacoustic active noise control and masking|2019|Integrates psychoacoustic ANC and masking; relevant to residual sound comfort in noise-canceling headphones.|
|A psychoacoustic active noise control system based on delayless subband adaptive filtering|2011|Subband implementation of psychoacoustic weighting to reduce computational cost while emphasizing sensitive bands.|
|Psychoacoustic study on active control system for kitchen hoods noise|2025|Recent real-time shaping ANC for kitchen hood noise using psychoacoustic measures; reinforces pleasant residual sound target.|
|Differentiable Psychoacoustic Models Applied in Active Noise Control|2024|Proposes differentiable psychoacoustic models in ANC optimization to shape residual noise for pleasantness.|
|Spatial Psychoacoustic Analysis of Perceptual Error Shaping in Active Noise Control|2025|Analyzes ANC perceptual error shaping using RMS, binaural loudness, sharpness, PEMO-Q, and MBSTOI under head movement scenarios.|
|A dual sampling-rate active noise equalization algorithm for active control of noise|2023|Active noise equalization algorithm that explicitly relates to loudness and sound-quality control.|
|A review of research on active noise control near human ear in complex sound field|2019|Review focused on ANC near the human ear; directly relevant to headphones where PNC cannot be changed.|
|Performance of personal active noise reduction devices|2012|Personal active noise reduction device performance; relevant to headphone comfort and limitations.|
|Analogue active noise control|2002|Feedback/analog ANC reference cited by headphone hybrid ANC; useful for low-frequency feedback constraints.|
|Hybrid feedforward-feedback active noise control|2004|Hybrid feedforward-feedback ANC basis for extending low-frequency attenuation.|
|Decoupling feedforward and feedback structures in hybrid active noise control systems|2008|Hybrid ANC decoupling reference; relevant to combining low-frequency feedback with perceptual feedforward paths.|
|Spatial active noise control based on kernel interpolation of sound field|2021|Spatial ANC method relevant to zone-of-comfort robustness and head position variation.|
|Multichannel Active Noise Control With Spatial Derivative Constraints to Enlarge the Quiet Zone|2024|Uses spatial derivative constraints to enlarge quiet zone; relevant to comfort robustness near ears.|
|Objective Signal Analysis for Investigating Feasibility of Active Noise Control in MRI|2022|Applies objective signal analysis to ANC feasibility; relevant to evaluating tonal/broadband noise constraints.|
|Active noise control of sound fields in rooms|1992|Foundational spatial ANC and room control; useful for limitations of cancellation zones.|
|Signal Processing for Active Control|2001|Foundational signal-processing reference for active noise/vibration control and robustness.|
|Active control of sound|1992|Foundational active sound control reference; helpful for physical feasibility boundaries.|
|Filtered-x LMS and filtered-u recursive LMS algorithms for active noise control|1990|Algorithmic ANC basis for later perceptual weighting and error shaping.|
|A filtered-X LMS algorithm for multichannel active sound control|1987|Classic filtered-X LMS paper, foundation for adaptive ANC controllers.|
|Fundamentals of Adaptive Filtering|2003|Adaptive filtering foundation cited by headphone ANC work.|
|Adaptive Signal Processing|1985|Classical LMS/adaptive filtering foundation for ANC algorithms.|
|Methods for calculating loudness|2017|Standard loudness calculation reference; relevant for objective residual loudness measurement.|
|DIN 45631/A1: Calculation of loudness level and loudness from the sound spectrum|2010|Standardized Zwicker loudness method including time-varying loudness; relevant to envelope comfort.|
|ECMA-418-2 Psychoacoustic metrics for ITT equipment|2022|Defines psychoacoustic metrics such as loudness, sharpness, roughness and tonality for sound quality evaluation.|
|A procedure for calculating auditory roughness|1982|Roughness metric foundation; relevant to modulation/envelope discomfort in residual noise.|
|Berechnungsverfahren für den sensorischen Wohlklang beliebiger Schallsignale|1985|Aures sensory pleasantness model combines psychoacoustic factors; cited by psychoacoustic ANC headphone work.|
|Procedure for calculating loudness of temporally variable sounds|2007|Time-varying loudness concepts underpin envelope constraints for comfortable ANC.|
|A model of loudness applicable to time-varying sounds|1997|Loudness model for time-varying sounds; relevant to attack/release and pumping comfort.|
|Modeling the loudness of sounds as perceived by normal-hearing and hearing-impaired listeners|2004|Loudness modeling reference; supports using auditory rather than SPL weighting.|
|Sharpness as an attribute of the timbre of steady sounds|1980|Sharpness foundation; relevant to high-Bark over-amplification guardrails.|
|An unbiased annoyance model for environmental noise|1971|Annoyance modeling background; relevant to comfort beyond loudness.|
|Sound quality metrics for automotive interior noise|2000|Automotive sound quality literature commonly uses loudness, sharpness, roughness, fluctuation strength and tonality.|
|Loudness: A measure of the response of the ear to sound|1933|Equal-loudness contour foundation; motivates frequency-dependent ANC weighting.|
|Normal equal-loudness-level contours|2003|Equal-loudness contour standard; relevant to Bark-specific weighting and high sensitivity regions.|
|ITU-R BS.468-4 Measurement of audio-frequency noise voltage level in sound broadcasting|1986|Noise weighting used in psychoacoustic ANC literature to prioritize perceptually sensitive frequency regions.|
