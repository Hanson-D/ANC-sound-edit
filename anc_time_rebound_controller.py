#!/usr/bin/env python3
"""
Control ANC rebound events in time while preserving non-target-band content.

This script splits TNC into:
  1. target band, for example 0-100 Hz
  2. residual signal outside that band

It computes short-window RMS for PNC and TNC inside the target band. When TNC is
above PNC + margin, it applies a smooth gain envelope to only the target-band
TNC component, then recombines it with the untouched residual.

Any time-domain gain change can alter spectrum. This script keeps that change
localized to the selected band and uses attack/release smoothing to reduce
extra spectral spread.
"""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

from anc_rebound_analyzer import (
    TimeReboundEvent,
    TimeReboundMetrics,
    band_limit_samples,
    detect_time_rebound_events,
    frame_rms_db,
    write_time_events_csv,
    write_time_metrics_csv,
)
from audio_band_limiter import EPS, nice_range, read_wav, svg_polyline, unique_output_path, write_wav


def validate_pair(pnc, tnc) -> None:
    if pnc.sample_rate != tnc.sample_rate:
        raise ValueError(f"sample rate mismatch: PNC={pnc.sample_rate}, TNC={tnc.sample_rate}")
    if pnc.samples.shape[1] != tnc.samples.shape[1]:
        raise ValueError(
            f"channel count mismatch: PNC={pnc.samples.shape[1]}, TNC={tnc.samples.shape[1]}"
        )


def smooth_frame_gain_db(
    target_gain_db: np.ndarray,
    hop_ms: float,
    attack_ms: float,
    release_ms: float,
) -> np.ndarray:
    if len(target_gain_db) == 0:
        return target_gain_db

    smoothed = np.empty_like(target_gain_db)
    current = 0.0
    hop_s = hop_ms / 1000.0
    attack_alpha = np.exp(-hop_s / max(attack_ms / 1000.0, EPS))
    release_alpha = np.exp(-hop_s / max(release_ms / 1000.0, EPS))

    for index, target in enumerate(target_gain_db):
        alpha = attack_alpha if target < current else release_alpha
        current = alpha * current + (1.0 - alpha) * target
        smoothed[index] = current
    return smoothed


def interpolate_gain_to_samples(
    frame_times_s: np.ndarray,
    frame_gain_db: np.ndarray,
    sample_rate: int,
    sample_count: int,
) -> np.ndarray:
    sample_times = np.arange(sample_count, dtype=np.float64) / sample_rate
    gain_db = np.interp(sample_times, frame_times_s, frame_gain_db, left=frame_gain_db[0], right=frame_gain_db[-1])
    return 10.0 ** (gain_db / 20.0)


def control_time_rebound(
    pnc_samples: np.ndarray,
    tnc_samples: np.ndarray,
    sample_rate: int,
    low_hz: float,
    high_hz: float,
    margin_db: float,
    window_ms: float,
    hop_ms: float,
    attack_ms: float,
    release_ms: float,
    max_attenuation_db: float,
    safety_db: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    min_len = min(len(pnc_samples), len(tnc_samples))
    pnc = pnc_samples[:min_len]
    tnc = tnc_samples[:min_len]

    pnc_band = band_limit_samples(pnc, sample_rate, low_hz, high_hz)
    tnc_band = band_limit_samples(tnc, sample_rate, low_hz, high_hz)
    residual = tnc - tnc_band

    frame_times_s, _, pnc_rms_db = frame_rms_db(pnc_band, sample_rate, window_ms, hop_ms)
    _, _, tnc_rms_db = frame_rms_db(tnc_band, sample_rate, window_ms, hop_ms)

    allowed_tnc_db = pnc_rms_db + margin_db - safety_db
    desired_gain_db = np.minimum(allowed_tnc_db - tnc_rms_db, 0.0)
    desired_gain_db = np.maximum(desired_gain_db, -abs(max_attenuation_db))
    applied_frame_gain_db = smooth_frame_gain_db(desired_gain_db, hop_ms, attack_ms, release_ms)
    sample_gain = interpolate_gain_to_samples(frame_times_s, applied_frame_gain_db, sample_rate, min_len)

    controlled_band = tnc_band * sample_gain[:, None]
    controlled = residual + controlled_band
    return controlled, frame_times_s, pnc_rms_db, tnc_rms_db, desired_gain_db, applied_frame_gain_db


def write_trace_csv(
    path: Path,
    frame_times_s: np.ndarray,
    pnc_rms_db: np.ndarray,
    tnc_rms_db: np.ndarray,
    controlled_rms_db: np.ndarray,
    desired_gain_db: np.ndarray,
    applied_gain_db: np.ndarray,
    margin_db: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "time_s",
        "pnc_band_rms_db",
        "original_tnc_band_rms_db",
        "controlled_tnc_band_rms_db",
        "original_rebound_above_margin_db",
        "controlled_rebound_above_margin_db",
        "desired_gain_db",
        "applied_gain_db",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, time_s in enumerate(frame_times_s):
            writer.writerow(
                {
                    "time_s": time_s,
                    "pnc_band_rms_db": pnc_rms_db[i],
                    "original_tnc_band_rms_db": tnc_rms_db[i],
                    "controlled_tnc_band_rms_db": controlled_rms_db[i],
                    "original_rebound_above_margin_db": max(tnc_rms_db[i] - pnc_rms_db[i] - margin_db, 0.0),
                    "controlled_rebound_above_margin_db": max(
                        controlled_rms_db[i] - pnc_rms_db[i] - margin_db,
                        0.0,
                    ),
                    "desired_gain_db": desired_gain_db[i],
                    "applied_gain_db": applied_gain_db[i],
                }
            )


def write_control_svg(
    path: Path,
    frame_times_s: np.ndarray,
    pnc_rms_db: np.ndarray,
    tnc_rms_db: np.ndarray,
    controlled_rms_db: np.ndarray,
    applied_gain_db: np.ndarray,
    margin_db: float,
    title: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1240, 760
    margin_l, margin_r = 82, 36
    plot_w = width - margin_l - margin_r
    rms_box = (margin_l, 92, plot_w, 280)
    gain_box = (margin_l, 478, plot_w, 170)
    x_range = (0.0, float(frame_times_s[-1]) if len(frame_times_s) else 1.0)
    rms_range = nice_range([pnc_rms_db, tnc_rms_db, controlled_rms_db])
    gain_range = (min(float(np.min(applied_gain_db)), -1.0), 0.5)

    def axes(box, y_label):
        x0, y0, w, h = box
        ticks = []
        for tick in np.linspace(x_range[0], x_range[1], 6):
            x = x0 + (tick - x_range[0]) / max(x_range[1] - x_range[0], EPS) * w
            ticks.append(
                f'<line x1="{x:.2f}" y1="{y0+h}" x2="{x:.2f}" y2="{y0+h+6}" stroke="#6b7280" />'
                f'<text x="{x:.2f}" y="{y0+h+24}" text-anchor="middle">{tick:.1f}</text>'
            )
        return (
            f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#ffffff" stroke="#d1d5db" />'
            f'{"".join(ticks)}'
            f'<text x="{x0 - 52}" y="{y0 + h / 2}" transform="rotate(-90 {x0 - 52},{y0 + h / 2})" '
            f'text-anchor="middle">{html.escape(y_label)}</text>'
        )

    def line(values, y_range, box, color, width_px=2.0):
        points = svg_polyline(frame_times_s, values, x_range, y_range, box)
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width_px}" />'

    ceiling = pnc_rms_db + margin_db
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; font-size: 14px; }}
.small {{ fill: #4b5563; font-size: 12px; }}
.title {{ font-size: 22px; font-weight: 650; }}
.section {{ font-size: 16px; font-weight: 650; }}
</style>
<rect width="100%" height="100%" fill="#f9fafb" />
<text class="title" x="40" y="42">{html.escape(title)}</text>
<text class="small" x="40" y="66">TNC target-band RMS is controlled against PNC + {margin_db:g} dB. Time axis is seconds.</text>
<text class="section" x="82" y="82">Target-band RMS envelope</text>
{axes(rms_box, "RMS dB")}
{line(pnc_rms_db, rms_range, rms_box, "#2563eb")}
{line(ceiling, rms_range, rms_box, "#6b7280", 1.6)}
{line(tnc_rms_db, rms_range, rms_box, "#d12f2f")}
{line(controlled_rms_db, rms_range, rms_box, "#111827", 2.4)}
<circle cx="694" cy="410" r="5" fill="#2563eb" /><text x="706" y="415">PNC</text>
<circle cx="760" cy="410" r="5" fill="#6b7280" /><text x="772" y="415">PNC + margin</text>
<circle cx="898" cy="410" r="5" fill="#d12f2f" /><text x="910" y="415">Original TNC</text>
<circle cx="1038" cy="410" r="5" fill="#111827" /><text x="1050" y="415">Controlled TNC</text>
<text x="82" y="438">Time (s)</text>
<text class="section" x="82" y="468">Applied target-band gain</text>
{axes(gain_box, "Gain dB")}
{line(applied_gain_db, gain_range, gain_box, "#111827", 2.4)}
<text x="82" y="686">Time (s)</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def summarize_metrics(metrics: Iterable[TimeReboundMetrics], source: str) -> TimeReboundMetrics:
    selected = [item for item in metrics if item.source == source]
    if len(selected) != 1:
        raise ValueError(f"expected one metrics row for {source}, got {len(selected)}")
    return selected[0]


def write_report_html(
    path: Path,
    svg_path: Path,
    metrics: List[TimeReboundMetrics],
    files: dict,
    low_hz: float,
    high_hz: float,
    margin_db: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = svg_path.read_text(encoding="utf-8")
    rows = []
    for item in metrics:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item.source)}</td>"
            f"<td>{item.event_count}</td>"
            f"<td>{item.total_event_duration_s:.3f}</td>"
            f"<td>{item.event_time_fraction:.3f}</td>"
            f"<td>{item.max_rebound_db:.2f}</td>"
            f"<td>{item.mean_positive_rebound_db:.2f}</td>"
            f"<td>{item.longest_event_s:.3f}</td>"
            "</tr>"
        )
    file_items = "".join(f"<li><code>{html.escape(name)}</code>: {html.escape(str(path))}</li>" for name, path in files.items())
    html_text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ANC Time Rebound Control</title>
<style>
body {{ margin: 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; }}
h1 {{ font-size: 26px; margin-bottom: 8px; }}
h2 {{ font-size: 18px; margin-top: 28px; }}
p, li {{ color: #374151; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th {{ background: #f3f4f6; }}
td:first-child, th:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>ANC Time Rebound Control</h1>
<p>Target band: <strong>{low_hz:g}-{high_hz:g} Hz</strong>. Control target: TNC target-band RMS no higher than PNC + <strong>{margin_db:g} dB</strong>.</p>
<p>The residual outside the target band is kept unchanged. The target-band component is controlled by a smooth gain envelope.</p>
<h2>Files</h2>
<ul>{file_items}</ul>
<h2>Time-domain Event Metrics</h2>
<table>
<thead>
<tr>
<th>source</th>
<th>event count</th>
<th>total duration s</th>
<th>time fraction</th>
<th>max rebound dB</th>
<th>mean positive dB</th>
<th>longest event s</th>
</tr>
</thead>
<tbody>{''.join(rows)}</tbody>
</table>
<h2>Control Curve</h2>
{svg}
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control time-domain ANC rebound by applying a smooth gain envelope to TNC's target band."
    )
    parser.add_argument("--pnc", type=Path, required=True, help="WAV recorded with headphones and ANC off")
    parser.add_argument("--tnc", type=Path, required=True, help="WAV recorded with headphones and ANC on")
    parser.add_argument("--low-hz", type=float, default=0.0)
    parser.add_argument("--high-hz", type=float, default=100.0)
    parser.add_argument("--margin-db", type=float, default=0.0)
    parser.add_argument("--time-window-ms", type=float, default=200.0)
    parser.add_argument("--time-hop-ms", type=float, default=25.0)
    parser.add_argument("--min-event-ms", type=float, default=100.0)
    parser.add_argument("--merge-gap-ms", type=float, default=50.0)
    parser.add_argument("--attack-ms", type=float, default=25.0)
    parser.add_argument("--release-ms", type=float, default=250.0)
    parser.add_argument("--max-attenuation-db", type=float, default=18.0)
    parser.add_argument(
        "--safety-db",
        type=float,
        default=0.0,
        help="control below PNC + margin by this extra amount to reduce residual event counts",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("out/anc_time_control"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.low_hz < 0 or args.high_hz <= args.low_hz:
        raise ValueError("--high-hz must be greater than --low-hz, and --low-hz must be non-negative")
    for name in ["time_window_ms", "time_hop_ms", "attack_ms", "release_ms"]:
        if getattr(args, name) <= 0:
            raise ValueError(f"--{name.replace('_', '-')} must be positive")
    if args.min_event_ms < 0 or args.merge_gap_ms < 0 or args.max_attenuation_db < 0 or args.safety_db < 0:
        raise ValueError("--min-event-ms, --merge-gap-ms, --max-attenuation-db, and --safety-db must be non-negative")

    pnc = read_wav(args.pnc)
    tnc = read_wav(args.tnc)
    validate_pair(pnc, tnc)
    if args.high_hz > tnc.sample_rate / 2:
        raise ValueError(f"--high-hz cannot exceed Nyquist frequency: {tnc.sample_rate / 2:g} Hz")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    controlled, frame_times_s, pnc_rms_db, tnc_rms_db, desired_gain_db, applied_gain_db = control_time_rebound(
        pnc.samples,
        tnc.samples,
        tnc.sample_rate,
        args.low_hz,
        args.high_hz,
        args.margin_db,
        args.time_window_ms,
        args.time_hop_ms,
        args.attack_ms,
        args.release_ms,
        args.max_attenuation_db,
        args.safety_db,
    )

    controlled_path = unique_output_path(args.output_dir / "tnc_time_rebound_controlled.wav")
    write_wav(controlled_path, controlled, tnc.sample_rate)

    controlled_band = band_limit_samples(controlled, tnc.sample_rate, args.low_hz, args.high_hz)
    _, _, controlled_rms_db = frame_rms_db(controlled_band, tnc.sample_rate, args.time_window_ms, args.time_hop_ms)
    trace_path = unique_output_path(args.output_dir / "time_control_trace.csv")
    write_trace_csv(
        trace_path,
        frame_times_s,
        pnc_rms_db,
        tnc_rms_db,
        controlled_rms_db,
        desired_gain_db,
        applied_gain_db,
        args.margin_db,
    )

    time_metrics, time_events = detect_time_rebound_events(
        pnc.samples,
        tnc.samples,
        controlled,
        tnc.sample_rate,
        args.low_hz,
        args.high_hz,
        args.margin_db,
        args.time_window_ms,
        args.time_hop_ms,
        args.min_event_ms,
        args.merge_gap_ms,
    )
    metrics_path = unique_output_path(args.output_dir / "time_rebound_metrics.csv")
    events_path = unique_output_path(args.output_dir / "time_rebound_events.csv")
    write_time_metrics_csv(metrics_path, time_metrics)
    write_time_events_csv(events_path, time_events)

    svg_path = unique_output_path(args.output_dir / "time_control.svg")
    write_control_svg(
        svg_path,
        frame_times_s,
        pnc_rms_db,
        tnc_rms_db,
        controlled_rms_db,
        applied_gain_db,
        args.margin_db,
        "ANC time-domain rebound control",
    )

    files = {
        "pnc": args.pnc,
        "tnc": args.tnc,
        "controlled_tnc": controlled_path,
        "trace_csv": trace_path,
        "metrics_csv": metrics_path,
        "events_csv": events_path,
        "svg": svg_path,
    }
    report_path = unique_output_path(args.output_dir / "time_control_report.html")
    write_report_html(report_path, svg_path, time_metrics, files, args.low_hz, args.high_hz, args.margin_db)

    original = summarize_metrics(time_metrics, "original_tnc")
    controlled_metrics = summarize_metrics(time_metrics, "processed_tnc")
    print(f"Wrote controlled WAV: {controlled_path}")
    print(f"Wrote report: {report_path}")
    print(f"Wrote trace CSV: {trace_path}")
    print(
        "Original TNC events: "
        f"{original.event_count}, total={original.total_event_duration_s:.3f}s, "
        f"max={original.max_rebound_db:.2f} dB"
    )
    print(
        "Controlled TNC events: "
        f"{controlled_metrics.event_count}, total={controlled_metrics.total_event_duration_s:.3f}s, "
        f"max={controlled_metrics.max_rebound_db:.2f} dB"
    )


if __name__ == "__main__":
    main()
