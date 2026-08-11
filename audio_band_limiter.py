#!/usr/bin/env python3
"""
Limit audio A to audio B's magnitude in a selected frequency band.

The tool reads two PCM WAV files, plots their overall magnitude/phase spectra,
and writes a processed copy of A. Inside the selected frequency band, each
short-time FFT bin in A is reduced to B's magnitude whenever A is higher.
"""

from __future__ import annotations

import argparse
import glob
import html
import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np


EPS = 1e-12
WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE
KSDATAFORMAT_SUBTYPE_PCM = bytes.fromhex("0100000000001000800000aa00389b71")
KSDATAFORMAT_SUBTYPE_IEEE_FLOAT = bytes.fromhex("0300000000001000800000aa00389b71")


@dataclass(frozen=True)
class WavAudio:
    samples: np.ndarray
    sample_rate: int


def read_wav(path: Path) -> WavAudio:
    resolved = resolve_input_path(path)
    fmt, channels, sample_rate, bits_per_sample, raw = read_wav_chunks(resolved)
    sample_width = (bits_per_sample + 7) // 8

    if fmt == WAVE_FORMAT_PCM and sample_width == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
        data = (data - 128.0) / 128.0
    elif fmt == WAVE_FORMAT_PCM and sample_width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif fmt == WAVE_FORMAT_PCM and sample_width == 3:
        data = pcm24_to_float(raw)
    elif fmt == WAVE_FORMAT_PCM and sample_width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    elif fmt == WAVE_FORMAT_IEEE_FLOAT and sample_width == 4:
        data = np.frombuffer(raw, dtype="<f4").astype(np.float64)
    elif fmt == WAVE_FORMAT_IEEE_FLOAT and sample_width == 8:
        data = np.frombuffer(raw, dtype="<f8").astype(np.float64)
    else:
        raise ValueError(
            f"{resolved}: unsupported WAV encoding format={fmt}, bits_per_sample={bits_per_sample}. "
            "Supported input: PCM 8/16/24/32-bit, IEEE float 32/64-bit, and WAVE_FORMAT_EXTENSIBLE with PCM/float subtype."
        )

    frame_values = (len(data) // channels) * channels
    if frame_values != len(data):
        data = data[:frame_values]
    samples = data.reshape(-1, channels)
    return WavAudio(samples=np.ascontiguousarray(samples), sample_rate=sample_rate)


def resolve_input_path(path: Path) -> Path:
    text = str(path)
    matches = glob.glob(text)
    if matches:
        return Path(matches[0])
    return path


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(1, 10000):
        candidate = path.with_name(f"{path.stem}_{index:03d}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"could not find available filename for {path}")


def read_wav_chunks(path: Path) -> Tuple[int, int, int, int, bytes]:
    with path.open("rb") as f:
        riff = f.read(12)
        if len(riff) != 12 or riff[:4] != b"RIFF" or riff[8:12] != b"WAVE":
            raise ValueError(f"{path}: not a RIFF/WAVE file")

        fmt_info = None
        data = None
        while True:
            header = f.read(8)
            if not header:
                break
            if len(header) != 8:
                raise ValueError(f"{path}: truncated WAV chunk header")
            chunk_id, chunk_size = header[:4], struct.unpack("<I", header[4:])[0]
            payload = f.read(chunk_size)
            if len(payload) != chunk_size:
                raise ValueError(f"{path}: truncated WAV chunk {chunk_id!r}")
            if chunk_size % 2:
                f.seek(1, 1)

            if chunk_id == b"fmt ":
                fmt_info = parse_fmt_chunk(path, payload)
            elif chunk_id == b"data":
                data = payload

        if fmt_info is None:
            raise ValueError(f"{path}: missing fmt chunk")
        if data is None:
            raise ValueError(f"{path}: missing data chunk")

    fmt, channels, sample_rate, bits_per_sample = fmt_info
    return fmt, channels, sample_rate, bits_per_sample, data


def parse_fmt_chunk(path: Path, payload: bytes) -> Tuple[int, int, int, int]:
    if len(payload) < 16:
        raise ValueError(f"{path}: invalid fmt chunk")
    fmt, channels, sample_rate, _byte_rate, block_align, bits_per_sample = struct.unpack("<HHIIHH", payload[:16])
    if channels <= 0 or sample_rate <= 0 or block_align <= 0:
        raise ValueError(f"{path}: invalid WAV fmt values")

    if fmt == WAVE_FORMAT_EXTENSIBLE:
        if len(payload) < 40:
            raise ValueError(f"{path}: invalid WAVE_FORMAT_EXTENSIBLE fmt chunk")
        subformat = payload[24:40]
        if subformat == KSDATAFORMAT_SUBTYPE_PCM:
            fmt = WAVE_FORMAT_PCM
        elif subformat == KSDATAFORMAT_SUBTYPE_IEEE_FLOAT:
            fmt = WAVE_FORMAT_IEEE_FLOAT
        else:
            raise ValueError(f"{path}: unsupported WAVE_FORMAT_EXTENSIBLE subtype {subformat.hex()}")

    return fmt, channels, sample_rate, bits_per_sample


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


def simplify_curve_log(
    freqs: np.ndarray,
    values: np.ndarray,
    max_points: int = 1800,
    min_hz: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    positive = np.asarray(freqs) >= min_hz
    freqs = np.asarray(freqs)[positive]
    values = np.asarray(values)[positive]
    if len(freqs) <= max_points:
        return freqs, values
    targets = np.geomspace(max(min_hz, float(freqs[0])), float(freqs[-1]), max_points)
    indexes = np.unique(np.searchsorted(freqs, targets).clip(0, len(freqs) - 1))
    return freqs[indexes], values[indexes]


def svg_polyline(
    freqs: np.ndarray,
    values: np.ndarray,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    box: Tuple[float, float, float, float],
    x_scale: str = "linear",
) -> str:
    x0, y0, width, height = box
    f0, f1 = x_range
    v0, v1 = y_range
    if x_scale == "log":
        safe_freqs = np.maximum(freqs, f0)
        x = x0 + (np.log10(safe_freqs) - np.log10(f0)) / max(np.log10(f1) - np.log10(f0), EPS) * width
    else:
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


def log_ticks(min_hz: float, max_hz: float) -> List[float]:
    ticks = []
    start_power = int(np.floor(np.log10(max(min_hz, EPS))))
    end_power = int(np.ceil(np.log10(max(max_hz, min_hz * 10.0))))
    for power in range(start_power, end_power + 1):
        for multiplier in (1, 2, 5):
            value = float(multiplier * (10 ** power))
            if min_hz <= value <= max_hz:
                ticks.append(value)
    return ticks


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

    max_freq = min(min(audio_a.sample_rate, audio_b.sample_rate) / 2.0, 22000.0)
    min_freq = 1.0
    visible = lambda f: (f >= min_freq) & (f <= max_freq)
    freqs_a, mag_a, phase_a = freqs_a[visible(freqs_a)], mag_a[visible(freqs_a)], phase_a[visible(freqs_a)]
    freqs_b, mag_b, phase_b = freqs_b[visible(freqs_b)], mag_b[visible(freqs_b)], phase_b[visible(freqs_b)]
    freqs_p, mag_p, phase_p = freqs_p[visible(freqs_p)], mag_p[visible(freqs_p)], phase_p[visible(freqs_p)]

    fa_m, ma = simplify_curve_log(freqs_a, mag_a, min_hz=min_freq)
    fb_m, mb = simplify_curve_log(freqs_b, mag_b, min_hz=min_freq)
    fp_m, mp = simplify_curve_log(freqs_p, mag_p, min_hz=min_freq)
    fa_p, pa = simplify_curve_log(freqs_a, phase_a, min_hz=min_freq)
    fb_p, pb = simplify_curve_log(freqs_b, phase_b, min_hz=min_freq)
    fp_p, pp = simplify_curve_log(freqs_p, phase_p, min_hz=min_freq)

    mag_range = nice_range([ma, mb, mp])
    phase_range = nice_range([pa, pb, pp])
    x_range = (min_freq, max_freq)
    width, height = 1200, 760
    margin_l, margin_r = 78, 34
    plot_w = width - margin_l - margin_r
    mag_box = (margin_l, 88, plot_w, 250)
    phase_box = (margin_l, 438, plot_w, 250)

    def line(freqs: np.ndarray, values: np.ndarray, yr: Tuple[float, float], box, color: str) -> str:
        points = svg_polyline(freqs, values, x_range, yr, box, x_scale="log")
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" />'

    def band_rect(box) -> str:
        x0, y0, w, h = box
        low = max(low_hz, x_range[0])
        high = min(high_hz, x_range[1])
        if high <= low:
            return ""
        bx = x0 + (np.log10(low) - np.log10(x_range[0])) / max(np.log10(x_range[1]) - np.log10(x_range[0]), EPS) * w
        bx1 = x0 + (np.log10(high) - np.log10(x_range[0])) / max(np.log10(x_range[1]) - np.log10(x_range[0]), EPS) * w
        bw = max(0, bx1 - bx)
        return f'<rect x="{bx:.2f}" y="{y0}" width="{bw:.2f}" height="{h}" fill="#f6c453" opacity="0.18" />'

    def axes(box, y_label: str) -> str:
        x0, y0, w, h = box
        ticks = log_ticks(x_range[0], x_range[1])
        tick_svg = []
        for tick in ticks:
            x = x0 + (np.log10(tick) - np.log10(x_range[0])) / max(np.log10(x_range[1]) - np.log10(x_range[0]), EPS) * w
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
<text x="78" y="374">Frequency (Hz, log scale)</text>
<circle cx="938" cy="360" r="5" fill="#d12f2f" /><text x="950" y="365">A original</text>
<circle cx="1034" cy="360" r="5" fill="#2563eb" /><text x="1046" y="365">B</text>
<circle cx="1084" cy="360" r="5" fill="#111827" /><text x="1096" y="365">A processed</text>
{axes(phase_box, "Phase rad")}
{band_rect(phase_box)}
{line(fa_p, pa, phase_range, phase_box, "#d12f2f")}
{line(fb_p, pb, phase_range, phase_box, "#2563eb")}
{line(fp_p, pp, phase_range, phase_box, "#111827")}
<text x="78" y="724">Frequency (Hz, log scale)</text>
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
    output_wav = unique_output_path(args.output_wav)
    plot_svg = unique_output_path(args.plot_svg)
    write_wav(output_wav, processed, audio_a.sample_rate)
    write_spectrum_svg(
        plot_svg,
        audio_a,
        audio_b,
        processed,
        args.low_hz,
        args.high_hz,
        "A limited to B in selected band",
    )

    print(f"Wrote processed WAV: {output_wav}")
    print(f"Wrote frequency/phase plot: {plot_svg}")
    print(f"Reduced STFT bins: {changed_bins}")


if __name__ == "__main__":
    main()
