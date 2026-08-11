#!/usr/bin/env python3
"""
Limit audio A to audio B's magnitude in a selected frequency band.

The tool reads two PCM WAV files, plots their overall magnitude/phase spectra,
and writes a processed copy of A. Inside the selected frequency band, each
short-time FFT bin in A is reduced to B's magnitude whenever A is higher.
"""

from __future__ import annotations

import argparse
import html
import math
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np


EPS = 1e-12


@dataclass(frozen=True)
class WavAudio:
    samples: np.ndarray
    sample_rate: int


def read_wav(path: Path) -> WavAudio:
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.getnframes()
        raw = wav.readframes(frames)

    if sample_width == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sample_width == 3:
        data = pcm24_to_float(raw)
    elif sample_width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"{path}: unsupported PCM sample width: {sample_width} bytes")

    samples = data.reshape(-1, channels)
    return WavAudio(samples=np.ascontiguousarray(samples), sample_rate=sample_rate)


def pcm24_to_float(raw: bytes) -> np.ndarray:
    bytes_ = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
    sign = (bytes_[:, 2] & 0x80) != 0
    padded = np.zeros((bytes_.shape[0], 4), dtype=np.uint8)
    padded[:, :3] = bytes_
    padded[sign, 3] = 0xFF
    return padded.view("<i4").reshape(-1).astype(np.float64) / 8388608.0


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    clipped = np.clip(samples, -1.0, 1.0 - (1.0 / 32768.0))
    pcm = (clipped * 32768.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(samples.shape[1])
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def hann_window(size: int) -> np.ndarray:
    return np.hanning(size).astype(np.float64)


def stft(signal: np.ndarray, frame_size: int, hop_size: int) -> np.ndarray:
    if signal.ndim != 1:
        raise ValueError("stft expects a mono signal")
    if len(signal) == 0:
        signal = np.zeros(1, dtype=np.float64)

    frame_count = max(1, int(math.ceil(max(0, len(signal) - frame_size) / hop_size)) + 1)
    padded_len = (frame_count - 1) * hop_size + frame_size
    padded = np.pad(signal, (0, padded_len - len(signal)))
    window = hann_window(frame_size)

    frames = np.empty((frame_count, frame_size), dtype=np.float64)
    for index in range(frame_count):
        start = index * hop_size
        frames[index] = padded[start : start + frame_size] * window
    return np.fft.rfft(frames, axis=1)


def istft(spectrum: np.ndarray, frame_size: int, hop_size: int, length: int) -> np.ndarray:
    frames = np.fft.irfft(spectrum, n=frame_size, axis=1)
    window = hann_window(frame_size)
    output_len = (spectrum.shape[0] - 1) * hop_size + frame_size
    output = np.zeros(output_len, dtype=np.float64)
    window_sum = np.zeros(output_len, dtype=np.float64)

    for index, frame in enumerate(frames):
        start = index * hop_size
        output[start : start + frame_size] += frame * window
        window_sum[start : start + frame_size] += window * window

    valid = window_sum > EPS
    output[valid] /= window_sum[valid]
    return output[:length]


def limit_a_to_b(
    audio_a: np.ndarray,
    audio_b: np.ndarray,
    sample_rate: int,
    low_hz: float,
    high_hz: float,
    frame_size: int,
    hop_size: int,
) -> Tuple[np.ndarray, int]:
    if audio_a.shape[1] != audio_b.shape[1]:
        raise ValueError(
            f"channel count mismatch: A has {audio_a.shape[1]}, B has {audio_b.shape[1]}"
        )

    output = np.zeros_like(audio_a)
    changed_bins = 0
    freqs = np.fft.rfftfreq(frame_size, d=1.0 / sample_rate)
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(band_mask):
        raise ValueError("selected band does not contain any FFT bins; increase frame size")

    target_len = max(len(audio_a), len(audio_b), frame_size)
    for channel in range(audio_a.shape[1]):
        a = np.pad(audio_a[:, channel], (0, target_len - len(audio_a)))
        b = np.pad(audio_b[:, channel], (0, target_len - len(audio_b)))
        spec_a = stft(a, frame_size, hop_size)
        spec_b = stft(b, frame_size, hop_size)

        mag_a = np.abs(spec_a[:, band_mask])
        mag_b = np.abs(spec_b[:, band_mask])
        over = mag_a > mag_b
        changed_bins += int(np.count_nonzero(over))

        scale = np.ones_like(mag_a)
        scale[over] = mag_b[over] / np.maximum(mag_a[over], EPS)
        spec_a[:, band_mask] *= scale
        output[:, channel] = istft(spec_a, frame_size, hop_size, len(audio_a))

    return output, changed_bins


def mono_mix(samples: np.ndarray) -> np.ndarray:
    return np.mean(samples, axis=1)


def spectrum_curve(samples: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mono = mono_mix(samples)
    if len(mono) == 0:
        mono = np.zeros(1)
    window = hann_window(len(mono))
    spec = np.fft.rfft(mono * window)
    freqs = np.fft.rfftfreq(len(mono), d=1.0 / sample_rate)
    magnitude_db = 20.0 * np.log10(np.maximum(np.abs(spec), EPS))
    phase = np.unwrap(np.angle(spec))
    return freqs, magnitude_db, phase


def simplify_curve(
    freqs: np.ndarray,
    values: np.ndarray,
    max_points: int = 1800,
) -> Tuple[np.ndarray, np.ndarray]:
    if len(freqs) <= max_points:
        return freqs, values
    indexes = np.unique(np.linspace(0, len(freqs) - 1, max_points).astype(int))
    return freqs[indexes], values[indexes]


def svg_polyline(
    freqs: np.ndarray,
    values: np.ndarray,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    box: Tuple[float, float, float, float],
) -> str:
    x0, y0, width, height = box
    f0, f1 = x_range
    v0, v1 = y_range
    x = x0 + (freqs - f0) / max(f1 - f0, EPS) * width
    y = y0 + height - (values - v0) / max(v1 - v0, EPS) * height
    points = " ".join(f"{px:.2f},{py:.2f}" for px, py in zip(x, y))
    return points


def nice_range(values: Iterable[np.ndarray], padding: float = 0.08) -> Tuple[float, float]:
    merged = np.concatenate([np.asarray(v) for v in values])
    merged = merged[np.isfinite(merged)]
    if len(merged) == 0:
        return -1.0, 1.0
    lo = float(np.percentile(merged, 1))
    hi = float(np.percentile(merged, 99))
    if abs(hi - lo) < EPS:
        return lo - 1.0, hi + 1.0
    pad = (hi - lo) * padding
    return lo - pad, hi + pad


def write_spectrum_svg(
    path: Path,
    audio_a: WavAudio,
    audio_b: WavAudio,
    processed: np.ndarray,
    low_hz: float,
    high_hz: float,
    title: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    freqs_a, mag_a, phase_a = spectrum_curve(audio_a.samples, audio_a.sample_rate)
    freqs_b, mag_b, phase_b = spectrum_curve(audio_b.samples, audio_b.sample_rate)
    freqs_p, mag_p, phase_p = spectrum_curve(processed, audio_a.sample_rate)

    max_freq = min(audio_a.sample_rate, audio_b.sample_rate) / 2.0
    visible = lambda f: f <= max_freq
    freqs_a, mag_a, phase_a = freqs_a[visible(freqs_a)], mag_a[visible(freqs_a)], phase_a[visible(freqs_a)]
    freqs_b, mag_b, phase_b = freqs_b[visible(freqs_b)], mag_b[visible(freqs_b)], phase_b[visible(freqs_b)]
    freqs_p, mag_p, phase_p = freqs_p[visible(freqs_p)], mag_p[visible(freqs_p)], phase_p[visible(freqs_p)]

    fa_m, ma = simplify_curve(freqs_a, mag_a)
    fb_m, mb = simplify_curve(freqs_b, mag_b)
    fp_m, mp = simplify_curve(freqs_p, mag_p)
    fa_p, pa = simplify_curve(freqs_a, phase_a)
    fb_p, pb = simplify_curve(freqs_b, phase_b)
    fp_p, pp = simplify_curve(freqs_p, phase_p)

    mag_range = nice_range([ma, mb, mp])
    phase_range = nice_range([pa, pb, pp])
    x_range = (0.0, max_freq)
    width, height = 1200, 760
    margin_l, margin_r = 78, 34
    plot_w = width - margin_l - margin_r
    mag_box = (margin_l, 88, plot_w, 250)
    phase_box = (margin_l, 438, plot_w, 250)

    def line(freqs: np.ndarray, values: np.ndarray, yr: Tuple[float, float], box, color: str) -> str:
        points = svg_polyline(freqs, values, x_range, yr, box)
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" />'

    def band_rect(box) -> str:
        x0, y0, w, h = box
        bx = x0 + (low_hz - x_range[0]) / max(x_range[1] - x_range[0], EPS) * w
        bw = (high_hz - low_hz) / max(x_range[1] - x_range[0], EPS) * w
        bx = max(x0, min(x0 + w, bx))
        bw = max(0, min(x0 + w - bx, bw))
        return f'<rect x="{bx:.2f}" y="{y0}" width="{bw:.2f}" height="{h}" fill="#f6c453" opacity="0.18" />'

    def axes(box, y_label: str) -> str:
        x0, y0, w, h = box
        ticks = [0, max_freq * 0.25, max_freq * 0.5, max_freq * 0.75, max_freq]
        tick_svg = []
        for tick in ticks:
            x = x0 + (tick / max_freq) * w if max_freq else x0
            label = f"{tick / 1000:.1f}k" if tick >= 1000 else f"{tick:.0f}"
            tick_svg.append(
                f'<line x1="{x:.2f}" y1="{y0+h}" x2="{x:.2f}" y2="{y0+h+6}" stroke="#6b7280" />'
                f'<text x="{x:.2f}" y="{y0+h+24}" text-anchor="middle">{label}</text>'
            )
        return (
            f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#ffffff" stroke="#d1d5db" />'
            f'{"".join(tick_svg)}'
            f'<text x="{x0 - 48}" y="{y0 + h / 2}" transform="rotate(-90 {x0 - 48},{y0 + h / 2})" '
            f'text-anchor="middle">{html.escape(y_label)}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; font-size: 14px; }}
.small {{ fill: #4b5563; font-size: 12px; }}
.title {{ font-size: 22px; font-weight: 650; }}
</style>
<rect width="100%" height="100%" fill="#f9fafb" />
<text class="title" x="40" y="42">{html.escape(title)}</text>
<text class="small" x="40" y="66">Yellow band: {low_hz:g} Hz to {high_hz:g} Hz. A is reduced only where A magnitude is above B.</text>
{axes(mag_box, "Magnitude dB")}
{band_rect(mag_box)}
{line(fa_m, ma, mag_range, mag_box, "#d12f2f")}
{line(fb_m, mb, mag_range, mag_box, "#2563eb")}
{line(fp_m, mp, mag_range, mag_box, "#111827")}
<text x="78" y="374">Frequency (Hz)</text>
<circle cx="938" cy="360" r="5" fill="#d12f2f" /><text x="950" y="365">A original</text>
<circle cx="1034" cy="360" r="5" fill="#2563eb" /><text x="1046" y="365">B</text>
<circle cx="1084" cy="360" r="5" fill="#111827" /><text x="1096" y="365">A processed</text>
{axes(phase_box, "Phase rad")}
{band_rect(phase_box)}
{line(fa_p, pa, phase_range, phase_box, "#d12f2f")}
{line(fb_p, pb, phase_range, phase_box, "#2563eb")}
{line(fp_p, pp, phase_range, phase_box, "#111827")}
<text x="78" y="724">Frequency (Hz)</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Limit WAV A to WAV B's magnitude where A exceeds B in a selected frequency band."
    )
    parser.add_argument("audio_a", type=Path, help="input WAV A; this is the audio that will be reduced")
    parser.add_argument("audio_b", type=Path, help="input WAV B; this is the ceiling/reference")
    parser.add_argument("--low-hz", type=float, required=True, help="lower edge of the processed band")
    parser.add_argument("--high-hz", type=float, required=True, help="upper edge of the processed band")
    parser.add_argument("--output-wav", type=Path, default=Path("out/a_limited_to_b.wav"))
    parser.add_argument("--plot-svg", type=Path, default=Path("out/frequency_phase.svg"))
    parser.add_argument("--frame-size", type=int, default=4096, help="STFT frame size")
    parser.add_argument("--hop-size", type=int, default=1024, help="STFT hop size")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.low_hz < 0 or args.high_hz <= args.low_hz:
        raise ValueError("--high-hz must be greater than --low-hz, and --low-hz must be non-negative")
    if args.frame_size <= 0 or args.hop_size <= 0:
        raise ValueError("--frame-size and --hop-size must be positive")

    audio_a = read_wav(args.audio_a)
    audio_b = read_wav(args.audio_b)
    if audio_a.sample_rate != audio_b.sample_rate:
        raise ValueError(f"sample rate mismatch: A={audio_a.sample_rate}, B={audio_b.sample_rate}")
    if args.high_hz > audio_a.sample_rate / 2:
        raise ValueError(f"--high-hz cannot exceed Nyquist frequency: {audio_a.sample_rate / 2:g} Hz")

    processed, changed_bins = limit_a_to_b(
        audio_a.samples,
        audio_b.samples,
        audio_a.sample_rate,
        args.low_hz,
        args.high_hz,
        args.frame_size,
        args.hop_size,
    )
    write_wav(args.output_wav, processed, audio_a.sample_rate)
    write_spectrum_svg(
        args.plot_svg,
        audio_a,
        audio_b,
        processed,
        args.low_hz,
        args.high_hz,
        "A limited to B in selected band",
    )

    print(f"Wrote processed WAV: {args.output_wav}")
    print(f"Wrote frequency/phase plot: {args.plot_svg}")
    print(f"Reduced STFT bins: {changed_bins}")


if __name__ == "__main__":
    main()
