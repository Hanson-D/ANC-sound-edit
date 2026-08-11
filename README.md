# ancadjust

Local workspace for research evidence collection, patent / industry application tracking, and evidence-graded database/report generation.

## Main Tool

- `research-evidence-vault/`: generic literature, patent, industry solution, product/application evidence vault workflow.
- `.claude/skills/research-evidence-vault/`: portable Agent skill wrapper for OpenCode, Claude Code, Codex, and similar agents.

## Current Project

- `research-evidence-vault/projects/anc/`: ANC benchmark project used to validate the workflow.

Run from this directory:

```bash
.claude/skills/research-evidence-vault/scripts/run_project_industry.sh research-evidence-vault/projects/anc "ANC patents mature solutions product noise isolation curves" "业界 ANC "
```

Verify:

```bash
.claude/skills/research-evidence-vault/scripts/verify.sh
```

## Audio A-to-B Band Limiter

`audio_band_limiter.py` compares two PCM WAV files. It draws A/B magnitude and
phase curves together, then creates a processed copy of A. In the selected
frequency band, whenever A's short-time FFT magnitude is higher than B's, A is
reduced to B's magnitude while keeping A's phase.

Example:

```bash
python3 audio_band_limiter.py input_a.wav input_b.wav \
  --low-hz 100 \
  --high-hz 1000 \
  --output-wav out/a_limited_to_b.wav \
  --plot-svg out/frequency_phase.svg
```

Notes:

- A and B must have the same sample rate and channel count.
- WAV input can be PCM WAV, IEEE float WAV, or common Windows
  `WAVE_FORMAT_EXTENSIBLE` PCM/float WAV. Output is 16-bit PCM WAV.
- `--frame-size` controls frequency resolution. Larger values give finer
  frequency bins but less time precision.
- On Windows command line, wrap paths with spaces in quotes, for example
  `"C:\Users\me\Desktop\PNC file.wav"`. The GUI file picker handles paths
  directly.

## ANC Rebound Analyzer

`anc_rebound_analyzer.py` is for the three-recording ANC workflow:

- OpenEar: no headphone.
- PNC: headphone on, ANC off.
- TNC: headphone on, ANC on.

It treats `TNC > PNC + margin` inside the selected band as rebound, creates
limited TNC experiment WAVs, and writes an HTML report, SVG curves, and CSV
metrics.

Example:

```bash
python3 anc_rebound_analyzer.py \
  --open-ear open_ear.wav \
  --pnc pnc.wav \
  --tnc tnc.wav \
  --low-hz 0 \
  --high-hz 100 \
  --margins-db 0,1,3 \
  --time-window-ms 200 \
  --time-hop-ms 25 \
  --min-event-ms 100 \
  --output-dir out/anc_rebound
```

Main outputs:

- `analysis_report.html`: summary table and curves.
- `rebound_metrics.csv`: max rebound, mean rebound, rebound area, worst frequency.
- `time_rebound_metrics.csv`: how many time-domain rebound events occurred, total
  event duration, longest event, and time-domain peak rebound.
- `time_rebound_events_margin_*.csv`: start/end time and peak value for each
  detected rebound event.
- `tnc_rebound_limited_margin_*.wav`: processed TNC versions for listening tests.
- `band_detail_margin_*.csv`: per-frequency values inside the selected band.

Time-domain events are detected after band-limiting PNC/TNC to the selected
frequency range. A rebound event starts when short-window TNC RMS is above
PNC RMS plus the margin, and adjacent active windows are merged into one event.

## ANC Time Rebound Controller

`anc_time_rebound_controller.py` creates a TNC version controlled in the time
domain. It keeps the signal outside the selected band unchanged, applies a
smooth gain envelope only to the selected-band TNC component, then recombines
the result.

This cannot preserve frequency information perfectly: any time-domain envelope
changes spectrum. The goal is to localize the change to the low-frequency band
and reduce envelope-driven rebound events with minimal extra spectral spread.

Example:

```bash
python3 anc_time_rebound_controller.py \
  --pnc pnc.wav \
  --tnc tnc.wav \
  --low-hz 0 \
  --high-hz 100 \
  --margin-db 0 \
  --time-window-ms 200 \
  --time-hop-ms 25 \
  --attack-ms 25 \
  --release-ms 250 \
  --safety-db 0 \
  --output-dir out/anc_time_control
```

Main outputs:

- `tnc_time_rebound_controlled.wav`: controlled TNC for listening tests.
- `time_control_report.html`: before/after event metrics and control curves.
- `time_control_trace.csv`: per-time-window RMS, rebound amount, and applied gain.
- `time_rebound_metrics.csv`: event-count summary before and after control.
- `time_rebound_events.csv`: start/end/peak details for each detected event.

If the goal is to reduce event count more aggressively, use a small safety
margin so the controller aims below the detection threshold:

```bash
python3 anc_time_rebound_controller.py \
  --pnc pnc.wav \
  --tnc tnc.wav \
  --low-hz 0 \
  --high-hz 100 \
  --margin-db 0 \
  --attack-ms 1 \
  --release-ms 50 \
  --safety-db 1 \
  --output-dir out/anc_time_control_fast
```

## Windows GUI App

`anc_rebound_gui.py` provides a desktop interface for selecting WAV files,
running analysis/control, viewing event metrics, and checking curves directly
inside the app.

Run as a Python app:

```bash
python anc_rebound_gui.py
```

Build a Windows executable on a Windows machine:

```bat
build_windows_exe.bat
```

The executable is created at:

```text
dist\ANCReboundTool.exe
```

The GUI has two main actions:

- `Run Full Analysis`: requires OpenEar, PNC, and TNC. Outputs the full
  frequency/time rebound report and processed TNC variants.
- `Run Time Control`: requires PNC and TNC. Outputs a time-domain controlled
  TNC WAV plus before/after event metrics.
- `运行 ANC 斜率平滑`: requires PNC and TNC. Outputs a modified TNC WAV after
  smoothing the selected ANC contribution slope segment.

## ANC Slope Flattener

`anc_slope_flattener.py` modifies the ANC contribution curve using the
frequency-domain definition:

```text
ANC contribution dB = PNC dB - TNC dB
```

It does not assume PNC and TNC are time-aligned. PNC is kept unchanged. The
script replaces a selected ANC contribution segment with a smoother transition,
then generates a modified TNC WAV by scaling TNC's frequency-domain magnitude.

Example:

```bash
python3 anc_slope_flattener.py \
  --pnc pnc.wav \
  --tnc tnc.wav \
  --start-hz 30 \
  --length-hz 50 \
  --start-depth-reduction-db 3 \
  --end-depth-reduction-db 0 \
  --start-transition-hz 10 \
  --end-transition-hz 10 \
  --mode smoothstep \
  --output-dir out/anc_slope
```

This replaces the ANC contribution segment from `30 Hz` to `80 Hz`.
The endpoint reduction options first make the selected endpoint ANC depth
shallower, then smooth between the adjusted endpoints. For example,
`--start-depth-reduction-db 3` reduces the start point's ANC depth by 3 dB
before generating the replacement curve.
`--start-transition-hz` and `--end-transition-hz` add smooth connection bands
before and after the replaced segment, avoiding abrupt jumps when endpoint
depth reduction is used.

Main outputs:

- `tnc_anc_slope_flattened.wav`: TNC WAV after ANC slope reshaping.
- `anc_slope_report.html`: before/target/after ANC curves and slope summary.
- `anc_slope_curve.svg`: visual curve comparison.
- `anc_slope_curve.csv`: per-frequency values inside the replaced range.

For a fixed start frequency and length, the endpoint-defined average slope may
not change much. The report therefore focuses on max local slope, p95 local
slope, effective transition width, and concentration ratio, which better
describe whether the drop is concentrated in a narrow part of the selected band.
