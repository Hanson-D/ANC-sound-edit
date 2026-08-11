#!/usr/bin/env python3
"""
Flatten a steep ANC contribution slope using frequency-domain ANC definition.

This script assumes PNC and TNC recordings are not time-aligned. It does not use
time-domain subtraction. Instead it defines:

  ANC contribution dB = PNC spectrum dB - TNC spectrum dB

Then it replaces a selected ANC contribution segment with a smoother curve and
generates a modified TNC WAV by scaling TNC STFT magnitudes while preserving TNC
phase. PNC is never modified.
"""

from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np

from audio_band_limiter import (
    EPS,
    istft,
    nice_range,
    read_wav,
    simplify_curve,
    spectrum_curve,
    stft,
    svg_polyline,
    write_wav,
)


def validate_pair(pnc, tnc) -> None:
    if pnc.sample_rate != tnc.sample_rate:
        raise ValueError(f"sample rate mismatch: PNC={pnc.sample_rate}, TNC={tnc.sample_rate}")
    if pnc.samples.shape[1] != tnc.samples.shape[1]:
        raise ValueError(
            f"channel count mismatch: PNC={pnc.samples.shape[1]}, TNC={tnc.samples.shape[1]}"
        )


def smoothstep(x: np.ndarray) -> np.ndarray:
    clipped = np.clip(x, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def make_replacement_curve(
    freqs: np.ndarray,
    anc_db: np.ndarray,
    start_hz: float,
    end_hz: float,
    mode: str,
) -> Tuple[np.ndarray, np.ndarray]:
    if start_hz < freqs[0] or end_hz > freqs[-1]:
        raise ValueError(f"selected range must be inside {freqs[0]:g}-{freqs[-1]:g} Hz")
    if end_hz <= start_hz:
        raise ValueError("end_hz must be greater than start_hz")

    start_value = float(np.interp(start_hz, freqs, anc_db))
    end_value = float(np.interp(end_hz, freqs, anc_db))
    target = anc_db.copy()
    band = (freqs >= start_hz) & (freqs <= end_hz)
    x = (freqs[band] - start_hz) / max(end_hz - start_hz, EPS)

    if mode == "linear":
        weight = x
    elif mode == "smoothstep":
        weight = smoothstep(x)
    else:
        raise ValueError("--mode must be smoothstep or linear")

    target[band] = start_value + (end_value - start_value) * weight
    return target, band


def mean_stft_magnitude_db(samples: np.ndarray, sample_rate: int, frame_size: int, hop_size: int) -> Tuple[np.ndarray, np.ndarray]:
    channel_curves = []
    for channel in range(samples.shape[1]):
        spec = stft(samples[:, channel], frame_size, hop_size)
        channel_curves.append(np.mean(np.abs(spec), axis=0))
    magnitude = np.mean(np.stack(channel_curves, axis=0), axis=0)
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate)
    return freqs, 20.0 * np.log10(np.maximum(magnitude, EPS))


def flatten_anc_slope(
    pnc_samples: np.ndarray,
    tnc_samples: np.ndarray,
    sample_rate: int,
    start_hz: float,
    length_hz: float,
    mode: str,
    frame_size: int,
    hop_size: int,
    max_boost_db: float,
    max_cut_db: float,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    end_hz = start_hz + length_hz
    freqs, pnc_db = mean_stft_magnitude_db(pnc_samples, sample_rate, frame_size, hop_size)
    _, tnc_db = mean_stft_magnitude_db(tnc_samples, sample_rate, frame_size, hop_size)
    original_anc_db = pnc_db - tnc_db
    target_anc_db, band = make_replacement_curve(freqs, original_anc_db, start_hz, end_hz, mode)
    target_tnc_db = pnc_db - target_anc_db
    gain_db = target_tnc_db - tnc_db
    gain_db = np.clip(gain_db, -abs(max_cut_db), abs(max_boost_db))
    gain = 10.0 ** (gain_db / 20.0)

    output = np.zeros_like(tnc_samples)
    for channel in range(tnc_samples.shape[1]):
        spec = stft(tnc_samples[:, channel], frame_size, hop_size)
        spec[:, band] *= gain[band][None, :]
        output[:, channel] = istft(spec, frame_size, hop_size, len(tnc_samples))

    _, modified_tnc_db = mean_stft_magnitude_db(output, sample_rate, frame_size, hop_size)
    modified_anc_db = pnc_db - modified_tnc_db
    curves = {
        "freq_hz": freqs,
        "pnc_db": pnc_db,
        "original_tnc_db": tnc_db,
        "modified_tnc_db": modified_tnc_db,
        "original_anc_db": original_anc_db,
        "target_anc_db": target_anc_db,
        "modified_anc_db": modified_anc_db,
        "gain_db": gain_db,
        "band_mask": band,
    }
    return output, curves


def slope_db_per_hz(freqs: np.ndarray, values: np.ndarray, start_hz: float, end_hz: float) -> float:
    start_value = float(np.interp(start_hz, freqs, values))
    end_value = float(np.interp(end_hz, freqs, values))
    return (end_value - start_value) / max(end_hz - start_hz, EPS)


def max_local_slope_db_per_hz(freqs: np.ndarray, values: np.ndarray, start_hz: float, end_hz: float) -> float:
    slopes = local_slopes_db_per_hz(freqs, values, start_hz, end_hz)
    return float(np.max(np.abs(slopes))) if len(slopes) else 0.0


def local_slopes_db_per_hz(freqs: np.ndarray, values: np.ndarray, start_hz: float, end_hz: float) -> np.ndarray:
    band = (freqs >= start_hz) & (freqs <= end_hz)
    band_freqs = freqs[band]
    band_values = values[band]
    if len(band_freqs) < 2:
        return np.zeros(0, dtype=np.float64)
    return np.diff(band_values) / np.maximum(np.diff(band_freqs), EPS)


def slope_shape_metrics(
    freqs: np.ndarray,
    values: np.ndarray,
    start_hz: float,
    end_hz: float,
) -> Dict[str, float]:
    avg = slope_db_per_hz(freqs, values, start_hz, end_hz)
    slopes = np.abs(local_slopes_db_per_hz(freqs, values, start_hz, end_hz))
    total_change = abs(float(np.interp(end_hz, freqs, values) - np.interp(start_hz, freqs, values)))
    if len(slopes) == 0:
        return {
            "average_slope": avg,
            "max_local_slope": 0.0,
            "p95_local_slope": 0.0,
            "effective_transition_width_hz": 0.0,
            "concentration_ratio": 0.0,
        }
    max_local = float(np.max(slopes))
    p95 = float(np.percentile(slopes, 95))
    average_abs = total_change / max(end_hz - start_hz, EPS)
    effective_width = total_change / max(max_local, EPS)
    concentration = max_local / max(average_abs, EPS)
    return {
        "average_slope": avg,
        "max_local_slope": max_local,
        "p95_local_slope": p95,
        "effective_transition_width_hz": effective_width,
        "concentration_ratio": concentration,
    }


def write_curve_csv(path: Path, curves: Dict[str, np.ndarray], start_hz: float, end_hz: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    freqs = curves["freq_hz"]
    band = (freqs >= start_hz) & (freqs <= end_hz)
    fieldnames = [
        "freq_hz",
        "pnc_db",
        "original_tnc_db",
        "modified_tnc_db",
        "original_anc_db",
        "target_anc_db",
        "modified_anc_db",
        "gain_db",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in np.flatnonzero(band):
            writer.writerow({name: curves[name][i] if name != "freq_hz" else freqs[i] for name in fieldnames})


def write_svg(path: Path, curves: Dict[str, np.ndarray], start_hz: float, end_hz: float, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    freqs = curves["freq_hz"]
    max_freq = min(max(end_hz * 2.0, end_hz + 100.0, 200.0), float(freqs[-1]))
    visible = freqs <= max_freq
    x_range = (0.0, max_freq)
    width, height = 1240, 820
    margin_l, margin_r = 82, 36
    plot_w = width - margin_l - margin_r
    anc_box = (margin_l, 92, plot_w, 280)
    tnc_box = (margin_l, 500, plot_w, 190)

    anc_series = []
    for key, color, label in [
        ("original_anc_db", "#d12f2f", "Original ANC"),
        ("target_anc_db", "#2563eb", "Target ANC"),
        ("modified_anc_db", "#111827", "Modified ANC"),
    ]:
        f, v = simplify_curve(freqs[visible], curves[key][visible])
        anc_series.append((f, v, color, label))

    tnc_series = []
    for key, color, label in [
        ("pnc_db", "#6b7280", "PNC"),
        ("original_tnc_db", "#d12f2f", "Original TNC"),
        ("modified_tnc_db", "#111827", "Modified TNC"),
    ]:
        f, v = simplify_curve(freqs[visible], curves[key][visible])
        tnc_series.append((f, v, color, label))

    anc_range = nice_range([item[1] for item in anc_series])
    tnc_range = nice_range([item[1] for item in tnc_series])

    def axes(box, y_label):
        x0, y0, w, h = box
        ticks = []
        for tick in np.linspace(x_range[0], x_range[1], 6):
            x = x0 + (tick - x_range[0]) / max(x_range[1] - x_range[0], EPS) * w
            ticks.append(
                f'<line x1="{x:.2f}" y1="{y0+h}" x2="{x:.2f}" y2="{y0+h+6}" stroke="#6b7280" />'
                f'<text x="{x:.2f}" y="{y0+h+24}" text-anchor="middle">{tick:.0f}</text>'
            )
        return (
            f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#ffffff" stroke="#d1d5db" />'
            f'{"".join(ticks)}'
            f'<text x="{x0 - 52}" y="{y0 + h / 2}" transform="rotate(-90 {x0 - 52},{y0 + h / 2})" '
            f'text-anchor="middle">{html.escape(y_label)}</text>'
        )

    def band_rect(box):
        x0, y0, w, h = box
        bx = x0 + (start_hz - x_range[0]) / max(x_range[1] - x_range[0], EPS) * w
        bw = (end_hz - start_hz) / max(x_range[1] - x_range[0], EPS) * w
        return f'<rect x="{bx:.2f}" y="{y0}" width="{bw:.2f}" height="{h}" fill="#f6c453" opacity="0.18" />'

    def line(freq, values, y_range, box, color, width_px=2.0):
        return (
            f'<polyline points="{svg_polyline(freq, values, x_range, y_range, box)}" '
            f'fill="none" stroke="{color}" stroke-width="{width_px}" />'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; font-size: 14px; }}
.small {{ fill: #4b5563; font-size: 12px; }}
.title {{ font-size: 22px; font-weight: 650; }}
.section {{ font-size: 16px; font-weight: 650; }}
</style>
<rect width="100%" height="100%" fill="#f9fafb" />
<text class="title" x="40" y="42">{html.escape(title)}</text>
<text class="small" x="40" y="66">ANC contribution is PNC dB - TNC dB. Yellow band is the replaced slope segment.</text>
<text class="section" x="82" y="82">ANC contribution curve</text>
{axes(anc_box, "ANC dB")}
{band_rect(anc_box)}
{''.join(line(f, v, anc_range, anc_box, c, 2.4 if label == "Modified ANC" else 2.0) for f, v, c, label in anc_series)}
<circle cx="806" cy="410" r="5" fill="#d12f2f" /><text x="818" y="415">Original ANC</text>
<circle cx="938" cy="410" r="5" fill="#2563eb" /><text x="950" y="415">Target ANC</text>
<circle cx="1058" cy="410" r="5" fill="#111827" /><text x="1070" y="415">Modified ANC</text>
<text x="82" y="438">Frequency (Hz)</text>
<text class="section" x="82" y="490">PNC and TNC spectra</text>
{axes(tnc_box, "Magnitude dB")}
{band_rect(tnc_box)}
{''.join(line(f, v, tnc_range, tnc_box, c, 2.4 if label == "Modified TNC" else 2.0) for f, v, c, label in tnc_series)}
<circle cx="788" cy="728" r="5" fill="#6b7280" /><text x="800" y="733">PNC</text>
<circle cx="852" cy="728" r="5" fill="#d12f2f" /><text x="864" y="733">Original TNC</text>
<circle cx="990" cy="728" r="5" fill="#111827" /><text x="1002" y="733">Modified TNC</text>
<text x="82" y="728">Frequency (Hz)</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def write_report_html(
    path: Path,
    svg_path: Path,
    pnc_path: Path,
    tnc_path: Path,
    output_wav: Path,
    curves: Dict[str, np.ndarray],
    start_hz: float,
    end_hz: float,
    mode: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    freqs = curves["freq_hz"]
    metric_rows = [
        ("Original ANC", slope_shape_metrics(freqs, curves["original_anc_db"], start_hz, end_hz)),
        ("Target ANC", slope_shape_metrics(freqs, curves["target_anc_db"], start_hz, end_hz)),
        ("Modified ANC", slope_shape_metrics(freqs, curves["modified_anc_db"], start_hz, end_hz)),
    ]
    table_rows = []
    for name, metrics in metric_rows:
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td>{metrics['average_slope']:.4f}</td>"
            f"<td>{metrics['max_local_slope']:.4f}</td>"
            f"<td>{metrics['p95_local_slope']:.4f}</td>"
            f"<td>{metrics['effective_transition_width_hz']:.2f}</td>"
            f"<td>{metrics['concentration_ratio']:.2f}</td>"
            "</tr>"
        )
    svg = svg_path.read_text(encoding="utf-8")
    html_text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ANC Slope Flattening Report</title>
<style>
body {{ margin: 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; }}
h1 {{ font-size: 26px; margin-bottom: 8px; }}
h2 {{ font-size: 18px; margin-top: 28px; }}
p, li {{ color: #374151; line-height: 1.5; }}
table {{ border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th {{ background: #f3f4f6; }}
td:first-child, th:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>ANC Slope Flattening Report</h1>
<p>ANC definition: <code>PNC_dB - TNC_dB</code>. Replacement range: <strong>{start_hz:g}-{end_hz:g} Hz</strong>. Mode: <strong>{html.escape(mode)}</strong>.</p>
<p>Because start and end values are fixed, average slope is mostly a reference. The main steepness checks are max local slope, p95 local slope, effective transition width, and concentration ratio.</p>
<h2>Files</h2>
<ul>
<li><code>PNC</code>: {html.escape(str(pnc_path))}</li>
<li><code>Original TNC</code>: {html.escape(str(tnc_path))}</li>
<li><code>Modified TNC</code>: {html.escape(str(output_wav))}</li>
</ul>
<h2>Slope Summary</h2>
<table>
<thead><tr><th>Curve</th><th>Average dB/Hz</th><th>Max local dB/Hz</th><th>P95 local dB/Hz</th><th>Effective width Hz</th><th>Concentration ratio</th></tr></thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>
<h2>Curves</h2>
{svg}
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flatten selected ANC contribution slope using PNC_dB - TNC_dB definition."
    )
    parser.add_argument("--pnc", type=Path, required=True, help="PNC WAV, headphones on and ANC off")
    parser.add_argument("--tnc", type=Path, required=True, help="TNC WAV, headphones on and ANC on")
    parser.add_argument("--start-hz", type=float, required=True, help="start frequency of the replaced segment")
    parser.add_argument("--length-hz", type=float, required=True, help="frequency length of the replaced segment")
    parser.add_argument("--mode", choices=["smoothstep", "linear"], default="smoothstep")
    parser.add_argument("--output-dir", type=Path, default=Path("out/anc_slope"))
    parser.add_argument("--frame-size", type=int, default=8192)
    parser.add_argument("--hop-size", type=int, default=2048)
    parser.add_argument("--max-boost-db", type=float, default=18.0)
    parser.add_argument("--max-cut-db", type=float, default=18.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start_hz < 0 or args.length_hz <= 0:
        raise ValueError("--start-hz must be non-negative and --length-hz must be positive")
    if args.frame_size <= 0 or args.hop_size <= 0:
        raise ValueError("--frame-size and --hop-size must be positive")

    pnc = read_wav(args.pnc)
    tnc = read_wav(args.tnc)
    validate_pair(pnc, tnc)
    end_hz = args.start_hz + args.length_hz
    if end_hz > tnc.sample_rate / 2:
        raise ValueError(f"selected end frequency cannot exceed Nyquist: {tnc.sample_rate / 2:g} Hz")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    modified_tnc, curves = flatten_anc_slope(
        pnc.samples,
        tnc.samples,
        tnc.sample_rate,
        args.start_hz,
        args.length_hz,
        args.mode,
        args.frame_size,
        args.hop_size,
        args.max_boost_db,
        args.max_cut_db,
    )

    output_wav = args.output_dir / "tnc_anc_slope_flattened.wav"
    csv_path = args.output_dir / "anc_slope_curve.csv"
    svg_path = args.output_dir / "anc_slope_curve.svg"
    report_path = args.output_dir / "anc_slope_report.html"
    write_wav(output_wav, modified_tnc, tnc.sample_rate)
    write_curve_csv(csv_path, curves, args.start_hz, end_hz)
    write_svg(svg_path, curves, args.start_hz, end_hz, "ANC slope flattening")
    write_report_html(report_path, svg_path, args.pnc, args.tnc, output_wav, curves, args.start_hz, end_hz, args.mode)

    freqs = curves["freq_hz"]
    print(f"Wrote modified TNC WAV: {output_wav}")
    print(f"Wrote report: {report_path}")
    print(f"Wrote curve CSV: {csv_path}")
    for name, key in [
        ("Original ANC", "original_anc_db"),
        ("Target ANC", "target_anc_db"),
        ("Modified ANC", "modified_anc_db"),
    ]:
        metrics = slope_shape_metrics(freqs, curves[key], args.start_hz, end_hz)
        print(
            f"{name}: avg={metrics['average_slope']:.4f} dB/Hz, "
            f"max_local={metrics['max_local_slope']:.4f} dB/Hz, "
            f"p95={metrics['p95_local_slope']:.4f} dB/Hz, "
            f"effective_width={metrics['effective_transition_width_hz']:.2f} Hz, "
            f"concentration={metrics['concentration_ratio']:.2f}"
        )


if __name__ == "__main__":
    main()
