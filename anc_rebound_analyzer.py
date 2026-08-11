#!/usr/bin/env python3
"""
Analyze and limit low-frequency ANC rebound from OpenEar, PNC, and TNC WAVs.

Definitions used here:
  PNC attenuation = OpenEar dB - PNC dB
  TNC attenuation = OpenEar dB - TNC dB
  ANC contribution = PNC dB - TNC dB
  Rebound = max(TNC dB - PNC dB - margin dB, 0)

When limiting, TNC is reduced only in the selected frequency band and only where
its short-time FFT magnitude is above PNC + margin dB. TNC phase is preserved.
"""

from __future__ import annotations

import argparse
import csv
import html
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

from audio_band_limiter import (
    EPS,
    WavAudio,
    istft,
    nice_range,
    read_wav,
    simplify_curve,
    spectrum_curve,
    stft,
    svg_polyline,
    write_wav,
)


@dataclass(frozen=True)
class ReboundMetrics:
    margin_db: float
    max_rebound_db: float
    mean_positive_rebound_db: float
    mean_rebound_db_over_band: float
    rebound_bin_fraction: float
    rebound_area_db_hz: float
    worst_frequency_hz: float
    mean_anc_contribution_db: float
    min_anc_contribution_db: float
    changed_stft_bins: int


@dataclass(frozen=True)
class TimeReboundEvent:
    source: str
    event_index: int
    start_s: float
    end_s: float
    duration_s: float
    peak_rebound_db: float
    mean_rebound_db: float
    peak_time_s: float


@dataclass(frozen=True)
class TimeReboundMetrics:
    margin_db: float
    source: str
    event_count: int
    total_event_duration_s: float
    event_time_fraction: float
    max_rebound_db: float
    mean_positive_rebound_db: float
    mean_event_peak_rebound_db: float
    longest_event_s: float


def validate_inputs(open_ear: WavAudio, pnc: WavAudio, tnc: WavAudio) -> None:
    sample_rates = {open_ear.sample_rate, pnc.sample_rate, tnc.sample_rate}
    if len(sample_rates) != 1:
        raise ValueError(
            "sample rate mismatch: "
            f"OpenEar={open_ear.sample_rate}, PNC={pnc.sample_rate}, TNC={tnc.sample_rate}"
        )

    channel_counts = {open_ear.samples.shape[1], pnc.samples.shape[1], tnc.samples.shape[1]}
    if len(channel_counts) != 1:
        raise ValueError(
            "channel count mismatch: "
            f"OpenEar={open_ear.samples.shape[1]}, PNC={pnc.samples.shape[1]}, "
            f"TNC={tnc.samples.shape[1]}"
        )


def limit_tnc_rebound(
    pnc_samples: np.ndarray,
    tnc_samples: np.ndarray,
    sample_rate: int,
    low_hz: float,
    high_hz: float,
    margin_db: float,
    frame_size: int,
    hop_size: int,
) -> Tuple[np.ndarray, int]:
    output = np.zeros_like(tnc_samples)
    changed_bins = 0
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate)
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(band_mask):
        raise ValueError("selected band does not contain any FFT bins; increase frame size")

    target_len = max(len(pnc_samples), len(tnc_samples), frame_size)
    margin_gain = 10.0 ** (margin_db / 20.0)

    for channel in range(tnc_samples.shape[1]):
        pnc = np.pad(pnc_samples[:, channel], (0, target_len - len(pnc_samples)))
        tnc = np.pad(tnc_samples[:, channel], (0, target_len - len(tnc_samples)))
        spec_pnc = stft(pnc, frame_size, hop_size)
        spec_tnc = stft(tnc, frame_size, hop_size)

        mag_pnc = np.abs(spec_pnc[:, band_mask])
        mag_tnc = np.abs(spec_tnc[:, band_mask])
        ceiling = mag_pnc * margin_gain
        over = mag_tnc > ceiling
        changed_bins += int(np.count_nonzero(over))

        scale = np.ones_like(mag_tnc)
        scale[over] = ceiling[over] / np.maximum(mag_tnc[over], EPS)
        spec_tnc[:, band_mask] *= scale
        output[:, channel] = istft(spec_tnc, frame_size, hop_size, len(tnc_samples))

    return output, changed_bins


def band_limit_samples(
    samples: np.ndarray,
    sample_rate: int,
    low_hz: float,
    high_hz: float,
) -> np.ndarray:
    freqs = np.fft.rfftfreq(len(samples), d=1.0 / sample_rate)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    output = np.zeros_like(samples)
    for channel in range(samples.shape[1]):
        spec = np.fft.rfft(samples[:, channel])
        spec[~mask] = 0.0
        output[:, channel] = np.fft.irfft(spec, n=len(samples))
    return output


def frame_rms_db(
    samples: np.ndarray,
    sample_rate: int,
    window_ms: float,
    hop_ms: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    window_size = max(1, int(round(sample_rate * window_ms / 1000.0)))
    hop_size = max(1, int(round(sample_rate * hop_ms / 1000.0)))
    if len(samples) < window_size:
        padded = np.pad(samples, ((0, window_size - len(samples)), (0, 0)))
    else:
        padded = samples

    frame_count = max(1, int(np.floor((len(padded) - window_size) / hop_size)) + 1)
    starts = np.arange(frame_count) * hop_size
    times = (starts + window_size / 2.0) / sample_rate
    rms = np.empty(frame_count, dtype=np.float64)
    for index, start in enumerate(starts):
        frame = padded[start : start + window_size]
        rms[index] = float(np.sqrt(np.mean(frame * frame)))
    return times, starts / sample_rate, 20.0 * np.log10(np.maximum(rms, EPS))


def merge_boolean_runs(
    active: np.ndarray,
    hop_s: float,
    merge_gap_ms: float,
) -> np.ndarray:
    if not np.any(active):
        return active

    merged = active.copy()
    max_gap_frames = int(round((merge_gap_ms / 1000.0) / max(hop_s, EPS)))
    if max_gap_frames <= 0:
        return merged

    true_indexes = np.flatnonzero(active)
    for left, right in zip(true_indexes[:-1], true_indexes[1:]):
        gap = right - left - 1
        if 0 < gap <= max_gap_frames:
            merged[left + 1 : right] = True
    return merged


def detect_time_rebound_events(
    pnc_samples: np.ndarray,
    tnc_samples: np.ndarray,
    processed_samples: np.ndarray,
    sample_rate: int,
    low_hz: float,
    high_hz: float,
    margin_db: float,
    window_ms: float,
    hop_ms: float,
    min_event_ms: float,
    merge_gap_ms: float,
) -> Tuple[List[TimeReboundMetrics], List[TimeReboundEvent]]:
    min_len = min(len(pnc_samples), len(tnc_samples), len(processed_samples))
    pnc_band = band_limit_samples(pnc_samples[:min_len], sample_rate, low_hz, high_hz)
    tnc_band = band_limit_samples(tnc_samples[:min_len], sample_rate, low_hz, high_hz)
    processed_band = band_limit_samples(processed_samples[:min_len], sample_rate, low_hz, high_hz)

    _, frame_starts_s, pnc_rms_db = frame_rms_db(pnc_band, sample_rate, window_ms, hop_ms)
    metrics: List[TimeReboundMetrics] = []
    events: List[TimeReboundEvent] = []

    for source, candidate in [("original_tnc", tnc_band), ("processed_tnc", processed_band)]:
        frame_times_s, _, candidate_rms_db = frame_rms_db(candidate, sample_rate, window_ms, hop_ms)
        rebound_db = candidate_rms_db - pnc_rms_db - margin_db
        positive_rebound_db = np.maximum(rebound_db, 0.0)
        active = merge_boolean_runs(positive_rebound_db > 0.0, hop_ms / 1000.0, merge_gap_ms)

        event_count = 0
        total_duration = 0.0
        event_peaks: List[float] = []
        longest_event = 0.0
        min_event_s = min_event_ms / 1000.0
        frame_duration_s = window_ms / 1000.0

        index = 0
        while index < len(active):
            if not active[index]:
                index += 1
                continue
            start_index = index
            while index + 1 < len(active) and active[index + 1]:
                index += 1
            end_index = index

            start_s = float(frame_starts_s[start_index])
            end_s = float(frame_starts_s[end_index] + frame_duration_s)
            duration_s = max(0.0, end_s - start_s)
            event_values = positive_rebound_db[start_index : end_index + 1]
            peak_offset = int(np.argmax(event_values))
            peak_db = float(event_values[peak_offset])

            if duration_s >= min_event_s and peak_db > 0.0:
                event_count += 1
                mean_db = float(np.mean(event_values[event_values > 0.0]))
                peak_time_s = float(frame_times_s[start_index + peak_offset])
                total_duration += duration_s
                longest_event = max(longest_event, duration_s)
                event_peaks.append(peak_db)
                events.append(
                    TimeReboundEvent(
                        source=source,
                        event_index=event_count,
                        start_s=start_s,
                        end_s=end_s,
                        duration_s=duration_s,
                        peak_rebound_db=peak_db,
                        mean_rebound_db=mean_db,
                        peak_time_s=peak_time_s,
                    )
                )
            index += 1

        positive_frames = positive_rebound_db[positive_rebound_db > 0.0]
        metrics.append(
            TimeReboundMetrics(
                margin_db=margin_db,
                source=source,
                event_count=event_count,
                total_event_duration_s=total_duration,
                event_time_fraction=total_duration / max(min_len / sample_rate, EPS),
                max_rebound_db=float(np.max(positive_rebound_db)),
                mean_positive_rebound_db=float(np.mean(positive_frames)) if len(positive_frames) else 0.0,
                mean_event_peak_rebound_db=float(np.mean(event_peaks)) if event_peaks else 0.0,
                longest_event_s=longest_event,
            )
        )

    return metrics, events


def common_spectrum(
    open_ear: WavAudio,
    pnc: WavAudio,
    tnc: WavAudio,
    processed: np.ndarray,
) -> Dict[str, np.ndarray]:
    min_len = min(len(open_ear.samples), len(pnc.samples), len(tnc.samples), len(processed))
    open_freqs, open_db, _ = spectrum_curve(open_ear.samples[:min_len], open_ear.sample_rate)
    pnc_freqs, pnc_db, _ = spectrum_curve(pnc.samples[:min_len], pnc.sample_rate)
    tnc_freqs, tnc_db, _ = spectrum_curve(tnc.samples[:min_len], tnc.sample_rate)
    processed_freqs, processed_db, _ = spectrum_curve(processed[:min_len], open_ear.sample_rate)

    if not (
        np.array_equal(open_freqs, pnc_freqs)
        and np.array_equal(open_freqs, tnc_freqs)
        and np.array_equal(open_freqs, processed_freqs)
    ):
        raise ValueError("internal frequency grid mismatch")

    return {
        "freq_hz": open_freqs,
        "open_db": open_db,
        "pnc_db": pnc_db,
        "tnc_db": tnc_db,
        "processed_db": processed_db,
    }


def compute_metrics(
    curves: Dict[str, np.ndarray],
    low_hz: float,
    high_hz: float,
    margin_db: float,
    changed_stft_bins: int,
) -> ReboundMetrics:
    freqs = curves["freq_hz"]
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(band_mask):
        raise ValueError("selected band does not contain any full-spectrum bins")

    band_freqs = freqs[band_mask]
    pnc_db = curves["pnc_db"][band_mask]
    tnc_db = curves["tnc_db"][band_mask]
    anc_contribution_db = pnc_db - tnc_db
    raw_rebound_db = tnc_db - pnc_db - margin_db
    positive_rebound_db = np.maximum(raw_rebound_db, 0.0)
    rebound_bins = positive_rebound_db > 0
    worst_index = int(np.argmax(positive_rebound_db))

    mean_positive = (
        float(np.mean(positive_rebound_db[rebound_bins])) if np.any(rebound_bins) else 0.0
    )
    area = float(np.trapz(positive_rebound_db, band_freqs)) if len(band_freqs) > 1 else 0.0

    return ReboundMetrics(
        margin_db=margin_db,
        max_rebound_db=float(np.max(positive_rebound_db)),
        mean_positive_rebound_db=mean_positive,
        mean_rebound_db_over_band=float(np.mean(positive_rebound_db)),
        rebound_bin_fraction=float(np.count_nonzero(rebound_bins) / len(positive_rebound_db)),
        rebound_area_db_hz=area,
        worst_frequency_hz=float(band_freqs[worst_index]),
        mean_anc_contribution_db=float(np.mean(anc_contribution_db)),
        min_anc_contribution_db=float(np.min(anc_contribution_db)),
        changed_stft_bins=changed_stft_bins,
    )


def write_metrics_csv(path: Path, metrics: Iterable[ReboundMetrics]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "margin_db",
        "max_rebound_db",
        "mean_positive_rebound_db",
        "mean_rebound_db_over_band",
        "rebound_bin_fraction",
        "rebound_area_db_hz",
        "worst_frequency_hz",
        "mean_anc_contribution_db",
        "min_anc_contribution_db",
        "changed_stft_bins",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in metrics:
            writer.writerow({name: getattr(item, name) for name in fieldnames})


def write_time_metrics_csv(path: Path, metrics: Iterable[TimeReboundMetrics]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "margin_db",
        "source",
        "event_count",
        "total_event_duration_s",
        "event_time_fraction",
        "max_rebound_db",
        "mean_positive_rebound_db",
        "mean_event_peak_rebound_db",
        "longest_event_s",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in metrics:
            writer.writerow({name: getattr(item, name) for name in fieldnames})


def write_time_events_csv(path: Path, events: Iterable[TimeReboundEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "event_index",
        "start_s",
        "end_s",
        "duration_s",
        "peak_rebound_db",
        "mean_rebound_db",
        "peak_time_s",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in events:
            writer.writerow({name: getattr(item, name) for name in fieldnames})


def write_band_csv(
    path: Path,
    curves: Dict[str, np.ndarray],
    low_hz: float,
    high_hz: float,
    margin_db: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    freqs = curves["freq_hz"]
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    fieldnames = [
        "freq_hz",
        "open_db",
        "pnc_db",
        "tnc_db",
        "processed_db",
        "pnc_attenuation_db",
        "tnc_attenuation_db",
        "processed_tnc_attenuation_db",
        "anc_contribution_db",
        "processed_anc_contribution_db",
        "rebound_above_margin_db",
        "processed_rebound_above_margin_db",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in np.flatnonzero(band_mask):
            row = {
                "freq_hz": curves["freq_hz"][i],
                "open_db": curves["open_db"][i],
                "pnc_db": curves["pnc_db"][i],
                "tnc_db": curves["tnc_db"][i],
                "processed_db": curves["processed_db"][i],
                "pnc_attenuation_db": curves["open_db"][i] - curves["pnc_db"][i],
                "tnc_attenuation_db": curves["open_db"][i] - curves["tnc_db"][i],
                "processed_tnc_attenuation_db": curves["open_db"][i] - curves["processed_db"][i],
                "anc_contribution_db": curves["pnc_db"][i] - curves["tnc_db"][i],
                "processed_anc_contribution_db": curves["pnc_db"][i] - curves["processed_db"][i],
                "rebound_above_margin_db": max(
                    curves["tnc_db"][i] - curves["pnc_db"][i] - margin_db, 0.0
                ),
                "processed_rebound_above_margin_db": max(
                    curves["processed_db"][i] - curves["pnc_db"][i] - margin_db, 0.0
                ),
            }
            writer.writerow(row)


def path_label(path: Path) -> str:
    return html.escape(str(path))


def write_rebound_svg(
    path: Path,
    curves: Dict[str, np.ndarray],
    low_hz: float,
    high_hz: float,
    margin_db: float,
    title: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    freqs = curves["freq_hz"]
    max_freq = max(high_hz * 2.5, high_hz + 200.0, 250.0)
    max_freq = min(max_freq, float(freqs[-1]))
    visible = freqs <= max_freq

    f_open, open_db = simplify_curve(freqs[visible], curves["open_db"][visible])
    f_pnc, pnc_db = simplify_curve(freqs[visible], curves["pnc_db"][visible])
    f_tnc, tnc_db = simplify_curve(freqs[visible], curves["tnc_db"][visible])
    f_processed, processed_db = simplify_curve(freqs[visible], curves["processed_db"][visible])
    f_rebound, rebound_db = simplify_curve(
        freqs[visible],
        np.maximum(curves["tnc_db"][visible] - curves["pnc_db"][visible] - margin_db, 0.0),
    )
    f_processed_rebound, processed_rebound_db = simplify_curve(
        freqs[visible],
        np.maximum(
            curves["processed_db"][visible] - curves["pnc_db"][visible] - margin_db,
            0.0,
        ),
    )

    db_range = nice_range([open_db, pnc_db, tnc_db, processed_db])
    rebound_range = (0.0, max(1.0, float(np.max([np.max(rebound_db), np.max(processed_rebound_db)])) * 1.15))
    x_range = (0.0, max_freq)

    width, height = 1240, 860
    margin_l, margin_r = 82, 36
    plot_w = width - margin_l - margin_r
    spectrum_box = (margin_l, 96, plot_w, 300)
    rebound_box = (margin_l, 510, plot_w, 230)

    def band_rect(box: Tuple[float, float, float, float]) -> str:
        x0, y0, w, h = box
        bx = x0 + (low_hz - x_range[0]) / max(x_range[1] - x_range[0], EPS) * w
        bw = (high_hz - low_hz) / max(x_range[1] - x_range[0], EPS) * w
        return f'<rect x="{bx:.2f}" y="{y0}" width="{bw:.2f}" height="{h}" fill="#f6c453" opacity="0.18" />'

    def axes(box: Tuple[float, float, float, float], y_label: str) -> str:
        x0, y0, w, h = box
        tick_values = np.linspace(0, max_freq, 6)
        ticks = []
        for tick in tick_values:
            x = x0 + (tick / max_freq) * w if max_freq else x0
            label = f"{tick:.0f}"
            ticks.append(
                f'<line x1="{x:.2f}" y1="{y0+h}" x2="{x:.2f}" y2="{y0+h+6}" stroke="#6b7280" />'
                f'<text x="{x:.2f}" y="{y0+h+24}" text-anchor="middle">{label}</text>'
            )
        return (
            f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#ffffff" stroke="#d1d5db" />'
            f'{"".join(ticks)}'
            f'<text x="{x0 - 52}" y="{y0 + h / 2}" transform="rotate(-90 {x0 - 52},{y0 + h / 2})" '
            f'text-anchor="middle">{html.escape(y_label)}</text>'
        )

    def line(freq: np.ndarray, values: np.ndarray, y_range, box, color: str, width_px: float = 2.0) -> str:
        points = svg_polyline(freq, values, x_range, y_range, box)
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width_px}" />'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; font-size: 14px; }}
.small {{ fill: #4b5563; font-size: 12px; }}
.title {{ font-size: 22px; font-weight: 650; }}
.section {{ font-size: 16px; font-weight: 650; }}
</style>
<rect width="100%" height="100%" fill="#f9fafb" />
<text class="title" x="40" y="42">{html.escape(title)}</text>
<text class="small" x="40" y="66">Band: {low_hz:g}-{high_hz:g} Hz. Rebound means TNC is above PNC + {margin_db:g} dB.</text>
<text class="section" x="82" y="86">OpenEar / PNC / TNC / processed TNC spectrum</text>
{axes(spectrum_box, "Magnitude dB")}
{band_rect(spectrum_box)}
{line(f_open, open_db, db_range, spectrum_box, "#6b7280")}
{line(f_pnc, pnc_db, db_range, spectrum_box, "#2563eb")}
{line(f_tnc, tnc_db, db_range, spectrum_box, "#d12f2f")}
{line(f_processed, processed_db, db_range, spectrum_box, "#111827", 2.4)}
<circle cx="736" cy="434" r="5" fill="#6b7280" /><text x="748" y="439">OpenEar</text>
<circle cx="840" cy="434" r="5" fill="#2563eb" /><text x="852" y="439">PNC</text>
<circle cx="910" cy="434" r="5" fill="#d12f2f" /><text x="922" y="439">TNC</text>
<circle cx="982" cy="434" r="5" fill="#111827" /><text x="994" y="439">Processed TNC</text>
<text x="82" y="462">Frequency (Hz)</text>
<text class="section" x="82" y="496">Rebound above PNC + margin</text>
{axes(rebound_box, "Rebound dB")}
{band_rect(rebound_box)}
{line(f_rebound, rebound_db, rebound_range, rebound_box, "#d12f2f", 2.4)}
{line(f_processed_rebound, processed_rebound_db, rebound_range, rebound_box, "#111827", 2.4)}
<circle cx="880" cy="778" r="5" fill="#d12f2f" /><text x="892" y="783">Original rebound</text>
<circle cx="1034" cy="778" r="5" fill="#111827" /><text x="1046" y="783">After limiting</text>
<text x="82" y="778">Frequency (Hz)</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def write_report_html(
    path: Path,
    metrics: List[ReboundMetrics],
    time_metrics: List[TimeReboundMetrics],
    svg_path: Path,
    files: Dict[str, Path],
    low_hz: float,
    high_hz: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg_content = svg_path.read_text(encoding="utf-8")

    rows = []
    for item in metrics:
        rows.append(
            "<tr>"
            f"<td>{item.margin_db:.2f}</td>"
            f"<td>{item.max_rebound_db:.2f}</td>"
            f"<td>{item.mean_positive_rebound_db:.2f}</td>"
            f"<td>{item.mean_rebound_db_over_band:.2f}</td>"
            f"<td>{item.rebound_bin_fraction:.3f}</td>"
            f"<td>{item.rebound_area_db_hz:.2f}</td>"
            f"<td>{item.worst_frequency_hz:.2f}</td>"
            f"<td>{item.mean_anc_contribution_db:.2f}</td>"
            f"<td>{item.min_anc_contribution_db:.2f}</td>"
            f"<td>{item.changed_stft_bins}</td>"
            "</tr>"
        )

    time_rows = []
    for item in time_metrics:
        time_rows.append(
            "<tr>"
            f"<td>{item.margin_db:.2f}</td>"
            f"<td>{html.escape(item.source)}</td>"
            f"<td>{item.event_count}</td>"
            f"<td>{item.total_event_duration_s:.3f}</td>"
            f"<td>{item.event_time_fraction:.3f}</td>"
            f"<td>{item.max_rebound_db:.2f}</td>"
            f"<td>{item.mean_positive_rebound_db:.2f}</td>"
            f"<td>{item.mean_event_peak_rebound_db:.2f}</td>"
            f"<td>{item.longest_event_s:.3f}</td>"
            "</tr>"
        )

    file_items = "".join(f"<li><code>{name}</code>: {path_label(value)}</li>" for name, value in files.items())
    html_text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ANC Rebound Analysis</title>
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
.figure {{ max-width: 1240px; }}
</style>
</head>
<body>
<h1>ANC Rebound Analysis</h1>
<p>Selected band: <strong>{low_hz:g}-{high_hz:g} Hz</strong>. Rebound is counted when TNC is higher than PNC plus the selected margin.</p>
<h2>Files</h2>
<ul>{file_items}</ul>
<h2>Metrics</h2>
<h3>Frequency-domain rebound</h3>
<table>
<thead>
<tr>
<th>margin dB</th>
<th>max rebound dB</th>
<th>mean positive dB</th>
<th>band mean dB</th>
<th>bin fraction</th>
<th>area dB*Hz</th>
<th>worst Hz</th>
<th>mean ANC contrib dB</th>
<th>min ANC contrib dB</th>
<th>changed STFT bins</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
<h3>Time-domain rebound events</h3>
<table>
<thead>
<tr>
<th>margin dB</th>
<th>source</th>
<th>event count</th>
<th>total duration s</th>
<th>time fraction</th>
<th>max rebound dB</th>
<th>mean positive dB</th>
<th>mean event peak dB</th>
<th>longest event s</th>
</tr>
</thead>
<tbody>
{''.join(time_rows)}
</tbody>
</table>
<h2>Curves</h2>
<div class="figure">{svg_content}</div>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def parse_float_list(value: str) -> List[float]:
    try:
        return [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected comma-separated numbers, e.g. 0,1,3") from exc


def safe_margin_name(value: float) -> str:
    text = f"{value:g}".replace("-", "minus_").replace(".", "p")
    return f"margin_{text}db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze OpenEar/PNC/TNC WAVs and limit low-frequency ANC rebound."
    )
    parser.add_argument("--open-ear", type=Path, required=True, help="WAV recorded without headphones")
    parser.add_argument("--pnc", type=Path, required=True, help="WAV recorded with headphones and ANC off")
    parser.add_argument("--tnc", type=Path, required=True, help="WAV recorded with headphones and ANC on")
    parser.add_argument("--low-hz", type=float, default=0.0)
    parser.add_argument("--high-hz", type=float, default=100.0)
    parser.add_argument(
        "--margins-db",
        type=parse_float_list,
        default=[0.0, 1.0, 3.0],
        help="comma-separated limiting margins to generate, default: 0,1,3",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("out/anc_rebound"))
    parser.add_argument("--frame-size", type=int, default=8192, help="STFT frame size")
    parser.add_argument("--hop-size", type=int, default=2048, help="STFT hop size")
    parser.add_argument("--time-window-ms", type=float, default=200.0, help="RMS window for time-event detection")
    parser.add_argument("--time-hop-ms", type=float, default=25.0, help="RMS hop for time-event detection")
    parser.add_argument("--min-event-ms", type=float, default=100.0, help="ignore shorter rebound events")
    parser.add_argument("--merge-gap-ms", type=float, default=50.0, help="merge events separated by shorter gaps")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.low_hz < 0 or args.high_hz <= args.low_hz:
        raise ValueError("--high-hz must be greater than --low-hz, and --low-hz must be non-negative")
    if args.frame_size <= 0 or args.hop_size <= 0:
        raise ValueError("--frame-size and --hop-size must be positive")
    if args.time_window_ms <= 0 or args.time_hop_ms <= 0:
        raise ValueError("--time-window-ms and --time-hop-ms must be positive")
    if args.min_event_ms < 0 or args.merge_gap_ms < 0:
        raise ValueError("--min-event-ms and --merge-gap-ms must be non-negative")
    if not args.margins_db:
        raise ValueError("--margins-db must include at least one value")

    open_ear = read_wav(args.open_ear)
    pnc = read_wav(args.pnc)
    tnc = read_wav(args.tnc)
    validate_inputs(open_ear, pnc, tnc)
    if args.high_hz > tnc.sample_rate / 2:
        raise ValueError(f"--high-hz cannot exceed Nyquist frequency: {tnc.sample_rate / 2:g} Hz")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics: List[ReboundMetrics] = []
    time_metrics: List[TimeReboundMetrics] = []
    first_curves = None
    first_svg = None
    output_files: Dict[str, Path] = {
        "open_ear": args.open_ear,
        "pnc": args.pnc,
        "tnc": args.tnc,
    }

    for index, margin_db in enumerate(args.margins_db):
        label = safe_margin_name(margin_db)
        processed, changed_bins = limit_tnc_rebound(
            pnc.samples,
            tnc.samples,
            tnc.sample_rate,
            args.low_hz,
            args.high_hz,
            margin_db,
            args.frame_size,
            args.hop_size,
        )
        wav_path = args.output_dir / f"tnc_rebound_limited_{label}.wav"
        write_wav(wav_path, processed, tnc.sample_rate)
        output_files[f"processed_tnc_{label}"] = wav_path

        curves = common_spectrum(open_ear, pnc, tnc, processed)
        item = compute_metrics(curves, args.low_hz, args.high_hz, margin_db, changed_bins)
        metrics.append(item)
        margin_time_metrics, time_events = detect_time_rebound_events(
            pnc.samples,
            tnc.samples,
            processed,
            tnc.sample_rate,
            args.low_hz,
            args.high_hz,
            margin_db,
            args.time_window_ms,
            args.time_hop_ms,
            args.min_event_ms,
            args.merge_gap_ms,
        )
        time_metrics.extend(margin_time_metrics)
        write_band_csv(args.output_dir / f"band_detail_{label}.csv", curves, args.low_hz, args.high_hz, margin_db)
        write_time_events_csv(args.output_dir / f"time_rebound_events_{label}.csv", time_events)
        svg_path = args.output_dir / f"curves_{label}.svg"
        write_rebound_svg(
            svg_path,
            curves,
            args.low_hz,
            args.high_hz,
            margin_db,
            f"ANC rebound analysis ({label})",
        )

        if index == 0:
            first_curves = curves
            first_svg = svg_path

    metrics_path = args.output_dir / "rebound_metrics.csv"
    write_metrics_csv(metrics_path, metrics)
    time_metrics_path = args.output_dir / "time_rebound_metrics.csv"
    write_time_metrics_csv(time_metrics_path, time_metrics)
    output_files["metrics_csv"] = metrics_path
    output_files["time_metrics_csv"] = time_metrics_path
    if first_svg is not None:
        output_files["primary_svg"] = first_svg
    if first_curves is not None:
        report_path = args.output_dir / "analysis_report.html"
        write_report_html(report_path, metrics, time_metrics, first_svg, output_files, args.low_hz, args.high_hz)
        output_files["html_report"] = report_path

    print(f"Wrote output directory: {args.output_dir}")
    print(f"Wrote metrics CSV: {metrics_path}")
    print(f"Wrote time metrics CSV: {time_metrics_path}")
    if first_svg is not None:
        print(f"Wrote primary curve SVG: {first_svg}")
    if first_curves is not None:
        print(f"Wrote HTML report: {args.output_dir / 'analysis_report.html'}")
    for item in metrics:
        print(
            f"margin={item.margin_db:g} dB, max_rebound={item.max_rebound_db:.2f} dB, "
            f"worst_freq={item.worst_frequency_hz:.2f} Hz, changed_bins={item.changed_stft_bins}"
        )
    for item in time_metrics:
        print(
            f"margin={item.margin_db:g} dB, {item.source}, time_events={item.event_count}, "
            f"total_event_duration={item.total_event_duration_s:.3f}s, "
            f"max_time_rebound={item.max_rebound_db:.2f} dB"
        )


if __name__ == "__main__":
    main()
