#!/usr/bin/env python3
"""
Tkinter GUI for ANC rebound analysis and time-domain control.

Build this on Windows with build_windows_exe.bat to create a standalone exe.
"""

from __future__ import annotations

import csv
import threading
import traceback
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

import numpy as np

from anc_rebound_analyzer import (
    common_spectrum,
    compute_metrics,
    detect_time_rebound_events,
    limit_tnc_rebound,
    safe_margin_name,
    validate_inputs,
    write_band_csv,
    write_metrics_csv,
    write_rebound_svg,
    write_report_html as write_analysis_report_html,
    write_time_events_csv,
    write_time_metrics_csv,
)
from anc_time_rebound_controller import (
    control_time_rebound,
    validate_pair,
    write_control_svg,
    write_report_html as write_control_report_html,
    write_trace_csv,
)
from anc_rebound_analyzer import band_limit_samples, frame_rms_db
from anc_slope_flattener import (
    flatten_anc_slope,
    max_local_slope_db_per_hz,
    slope_db_per_hz,
    slope_shape_metrics,
    write_curve_csv as write_slope_curve_csv,
    write_report_html as write_slope_report_html,
    write_svg as write_slope_svg,
)
from audio_band_limiter import read_wav, write_wav


APP_TITLE = "ANC 反弹分析与控制工具"


class AncReboundGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x780")
        self.minsize(980, 680)

        self.open_ear_var = tk.StringVar()
        self.pnc_var = tk.StringVar()
        self.tnc_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.cwd() / "out" / "anc_gui"))
        self.low_hz_var = tk.StringVar(value="0")
        self.high_hz_var = tk.StringVar(value="100")
        self.margins_var = tk.StringVar(value="0,1,3")
        self.margin_var = tk.StringVar(value="0")
        self.time_window_var = tk.StringVar(value="200")
        self.time_hop_var = tk.StringVar(value="25")
        self.min_event_var = tk.StringVar(value="100")
        self.merge_gap_var = tk.StringVar(value="50")
        self.attack_var = tk.StringVar(value="25")
        self.release_var = tk.StringVar(value="250")
        self.safety_var = tk.StringVar(value="0")
        self.max_atten_var = tk.StringVar(value="18")
        self.slope_start_var = tk.StringVar(value="30")
        self.slope_length_var = tk.StringVar(value="50")
        self.slope_mode_var = tk.StringVar(value="smoothstep")
        self.status_var = tk.StringVar(value="就绪")
        self.last_output_dir: Path | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        controls = ttk.Frame(root)
        controls.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        controls.columnconfigure(1, weight=1)

        self._file_row(controls, 0, "OpenEar", self.open_ear_var)
        self._file_row(controls, 1, "PNC", self.pnc_var)
        self._file_row(controls, 2, "TNC", self.tnc_var)
        self._dir_row(controls, 3, "Output", self.output_dir_var)

        params = ttk.LabelFrame(controls, text="参数", padding=10)
        params.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        for col in range(4):
            params.columnconfigure(col, weight=1)
        self._entry(params, 0, 0, "Low Hz", self.low_hz_var)
        self._entry(params, 0, 2, "High Hz", self.high_hz_var)
        self._entry(params, 1, 0, "Margins dB", self.margins_var)
        self._entry(params, 1, 2, "Control margin", self.margin_var)
        self._entry(params, 2, 0, "Window ms", self.time_window_var)
        self._entry(params, 2, 2, "Hop ms", self.time_hop_var)
        self._entry(params, 3, 0, "Min event ms", self.min_event_var)
        self._entry(params, 3, 2, "Merge gap ms", self.merge_gap_var)
        self._entry(params, 4, 0, "Attack ms", self.attack_var)
        self._entry(params, 4, 2, "Release ms", self.release_var)
        self._entry(params, 5, 0, "Safety dB", self.safety_var)
        self._entry(params, 5, 2, "Max atten dB", self.max_atten_var)
        self._entry(params, 6, 0, "Slope start Hz", self.slope_start_var)
        self._entry(params, 6, 2, "Slope length Hz", self.slope_length_var)
        ttk.Label(params, text="Slope mode").grid(row=7, column=0, sticky="w", pady=4, padx=(0, 6))
        ttk.Combobox(
            params,
            textvariable=self.slope_mode_var,
            values=("smoothstep", "linear"),
            width=9,
            state="readonly",
        ).grid(row=7, column=1, sticky="ew", pady=4)

        actions = ttk.Frame(controls)
        actions.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Button(actions, text="运行完整分析", command=self.run_full_analysis).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(actions, text="运行时域控制", command=self.run_time_control).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(actions, text="运行 ANC 斜率平滑", command=self.run_slope_flattening).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(actions, text="打开输出文件夹", command=self.open_output_folder).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(actions, text="打开 HTML 报告", command=self.open_report).pack(fill=tk.X)

        ttk.Label(controls, textvariable=self.status_var, wraplength=310).grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0)
        )

        right = ttk.Frame(root)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        tabs = ttk.Notebook(right)
        tabs.grid(row=0, column=0, sticky="nsew")

        self.summary = ttk.Frame(tabs, padding=8)
        self.chart_frame = ttk.Frame(tabs, padding=8)
        self.log_frame = ttk.Frame(tabs, padding=8)
        tabs.add(self.summary, text="指标")
        tabs.add(self.chart_frame, text="可视化")
        tabs.add(self.log_frame, text="日志")

        self.summary.rowconfigure(0, weight=1)
        self.summary.columnconfigure(0, weight=1)
        columns = ("kind", "margin", "source", "count", "duration", "max_db", "mean_db", "extra")
        self.metrics_table = ttk.Treeview(self.summary, columns=columns, show="headings")
        headings = {
            "kind": "类型",
            "margin": "Margin",
            "source": "来源/频点",
            "count": "次数",
            "duration": "持续时间",
            "max_db": "Max dB",
            "mean_db": "Mean dB",
            "extra": "Extra",
        }
        for col, text in headings.items():
            self.metrics_table.heading(col, text=text)
            self.metrics_table.column(col, width=110, anchor=tk.CENTER)
        self.metrics_table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.summary, orient=tk.VERTICAL, command=self.metrics_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.metrics_table.configure(yscrollcommand=scrollbar.set)

        self.chart_frame.rowconfigure(0, weight=1)
        self.chart_frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.chart_frame, bg="#f9fafb", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self.redraw_last_chart())
        self.last_chart = None

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _file_row(self, parent, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var, width=34).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(parent, text="Browse", command=lambda: self.pick_file(var)).grid(row=row, column=2, padx=(6, 0), pady=3)

    def _dir_row(self, parent, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var, width=34).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(parent, text="Browse", command=lambda: self.pick_dir(var)).grid(row=row, column=2, padx=(6, 0), pady=3)

    def _entry(self, parent, row: int, col: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=4, padx=(0, 6))
        ttk.Entry(parent, textvariable=var, width=11).grid(row=row, column=col + 1, sticky="ew", pady=4)

    def pick_file(self, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav *.WAV"), ("All files", "*.*")])
        if path:
            var.set(path)

    def pick_dir(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def read_common_params(self) -> dict:
        return {
            "low_hz": float(self.low_hz_var.get()),
            "high_hz": float(self.high_hz_var.get()),
            "window_ms": float(self.time_window_var.get()),
            "hop_ms": float(self.time_hop_var.get()),
            "min_event_ms": float(self.min_event_var.get()),
            "merge_gap_ms": float(self.merge_gap_var.get()),
            "output_dir": Path(self.output_dir_var.get()),
        }

    def run_full_analysis(self) -> None:
        self.run_in_worker(self._run_full_analysis)

    def run_time_control(self) -> None:
        self.run_in_worker(self._run_time_control)

    def run_slope_flattening(self) -> None:
        self.run_in_worker(self._run_slope_flattening)

    def run_in_worker(self, fn) -> None:
        thread = threading.Thread(target=self._worker_wrapper, args=(fn,), daemon=True)
        thread.start()

    def _worker_wrapper(self, fn) -> None:
        self.set_status("运行中...")
        try:
            result = fn()
            self.after(0, lambda: self.apply_result(result))
        except Exception:
            text = traceback.format_exc()
            self.after(0, lambda: self.show_error(text))

    def _run_full_analysis(self) -> dict:
        params = self.read_common_params()
        margins = [float(part.strip()) for part in self.margins_var.get().split(",") if part.strip()]
        if not margins:
            raise ValueError("Margins dB cannot be empty")

        open_ear = read_wav(Path(self.open_ear_var.get()))
        pnc = read_wav(Path(self.pnc_var.get()))
        tnc = read_wav(Path(self.tnc_var.get()))
        validate_inputs(open_ear, pnc, tnc)

        out_dir = params["output_dir"] / "full_analysis"
        out_dir.mkdir(parents=True, exist_ok=True)
        self.last_output_dir = out_dir

        freq_metrics = []
        time_metrics = []
        output_files = {"open_ear": Path(self.open_ear_var.get()), "pnc": Path(self.pnc_var.get()), "tnc": Path(self.tnc_var.get())}
        first_svg = None
        first_curves = None

        for index, margin in enumerate(margins):
            label = safe_margin_name(margin)
            processed, changed_bins = limit_tnc_rebound(
                pnc.samples,
                tnc.samples,
                tnc.sample_rate,
                params["low_hz"],
                params["high_hz"],
                margin,
                8192,
                2048,
            )
            wav_path = out_dir / f"tnc_rebound_limited_{label}.wav"
            write_wav(wav_path, processed, tnc.sample_rate)
            output_files[f"processed_tnc_{label}"] = wav_path

            curves = common_spectrum(open_ear, pnc, tnc, processed)
            metric = compute_metrics(curves, params["low_hz"], params["high_hz"], margin, changed_bins)
            freq_metrics.append(metric)
            tm, events = detect_time_rebound_events(
                pnc.samples,
                tnc.samples,
                processed,
                tnc.sample_rate,
                params["low_hz"],
                params["high_hz"],
                margin,
                params["window_ms"],
                params["hop_ms"],
                params["min_event_ms"],
                params["merge_gap_ms"],
            )
            time_metrics.extend(tm)
            write_band_csv(out_dir / f"band_detail_{label}.csv", curves, params["low_hz"], params["high_hz"], margin)
            write_time_events_csv(out_dir / f"time_rebound_events_{label}.csv", events)
            svg_path = out_dir / f"curves_{label}.svg"
            write_rebound_svg(svg_path, curves, params["low_hz"], params["high_hz"], margin, f"ANC rebound analysis ({label})")
            if index == 0:
                first_svg = svg_path
                first_curves = curves

        metrics_path = out_dir / "rebound_metrics.csv"
        time_metrics_path = out_dir / "time_rebound_metrics.csv"
        write_metrics_csv(metrics_path, freq_metrics)
        write_time_metrics_csv(time_metrics_path, time_metrics)
        output_files["metrics_csv"] = metrics_path
        output_files["time_metrics_csv"] = time_metrics_path
        output_files["primary_svg"] = first_svg
        report_path = out_dir / "analysis_report.html"
        write_analysis_report_html(report_path, freq_metrics, time_metrics, first_svg, output_files, params["low_hz"], params["high_hz"])
        output_files["html_report"] = report_path

        chart = self.make_frequency_chart(first_curves, params["low_hz"], params["high_hz"])
        return {"mode": "analysis", "output_dir": out_dir, "report": report_path, "freq": freq_metrics, "time": time_metrics, "chart": chart}

    def _run_time_control(self) -> dict:
        params = self.read_common_params()
        margin = float(self.margin_var.get())
        attack_ms = float(self.attack_var.get())
        release_ms = float(self.release_var.get())
        max_attenuation_db = float(self.max_atten_var.get())
        safety_db = float(self.safety_var.get())

        pnc = read_wav(Path(self.pnc_var.get()))
        tnc = read_wav(Path(self.tnc_var.get()))
        validate_pair(pnc, tnc)

        out_dir = params["output_dir"] / "time_control"
        out_dir.mkdir(parents=True, exist_ok=True)
        self.last_output_dir = out_dir

        controlled, frame_times_s, pnc_rms_db, tnc_rms_db, desired_gain_db, applied_gain_db = control_time_rebound(
            pnc.samples,
            tnc.samples,
            tnc.sample_rate,
            params["low_hz"],
            params["high_hz"],
            margin,
            params["window_ms"],
            params["hop_ms"],
            attack_ms,
            release_ms,
            max_attenuation_db,
            safety_db,
        )
        controlled_path = out_dir / "tnc_time_rebound_controlled.wav"
        write_wav(controlled_path, controlled, tnc.sample_rate)

        controlled_band = band_limit_samples(controlled, tnc.sample_rate, params["low_hz"], params["high_hz"])
        _, _, controlled_rms_db = frame_rms_db(controlled_band, tnc.sample_rate, params["window_ms"], params["hop_ms"])
        trace_path = out_dir / "time_control_trace.csv"
        write_trace_csv(trace_path, frame_times_s, pnc_rms_db, tnc_rms_db, controlled_rms_db, desired_gain_db, applied_gain_db, margin)

        time_metrics, events = detect_time_rebound_events(
            pnc.samples,
            tnc.samples,
            controlled,
            tnc.sample_rate,
            params["low_hz"],
            params["high_hz"],
            margin,
            params["window_ms"],
            params["hop_ms"],
            params["min_event_ms"],
            params["merge_gap_ms"],
        )
        metrics_path = out_dir / "time_rebound_metrics.csv"
        events_path = out_dir / "time_rebound_events.csv"
        write_time_metrics_csv(metrics_path, time_metrics)
        write_time_events_csv(events_path, events)

        svg_path = out_dir / "time_control.svg"
        write_control_svg(svg_path, frame_times_s, pnc_rms_db, tnc_rms_db, controlled_rms_db, applied_gain_db, margin, "ANC time-domain rebound control")
        report_path = out_dir / "time_control_report.html"
        files = {
            "pnc": Path(self.pnc_var.get()),
            "tnc": Path(self.tnc_var.get()),
            "controlled_tnc": controlled_path,
            "trace_csv": trace_path,
            "metrics_csv": metrics_path,
            "events_csv": events_path,
            "svg": svg_path,
        }
        write_control_report_html(report_path, svg_path, time_metrics, files, params["low_hz"], params["high_hz"], margin)

        chart = {
            "type": "time",
            "x": frame_times_s,
            "series": [
                ("PNC", pnc_rms_db, "#2563eb"),
                ("Original TNC", tnc_rms_db, "#d12f2f"),
                ("Controlled TNC", controlled_rms_db, "#111827"),
                ("Applied gain dB", applied_gain_db, "#0f766e"),
            ],
            "title": "Target-band RMS and applied gain",
        }
        return {"mode": "control", "output_dir": out_dir, "report": report_path, "time": time_metrics, "chart": chart}

    def _run_slope_flattening(self) -> dict:
        params = self.read_common_params()
        start_hz = float(self.slope_start_var.get())
        length_hz = float(self.slope_length_var.get())
        mode = self.slope_mode_var.get()
        pnc = read_wav(Path(self.pnc_var.get()))
        tnc = read_wav(Path(self.tnc_var.get()))
        validate_pair(pnc, tnc)

        out_dir = params["output_dir"] / "slope_flattening"
        out_dir.mkdir(parents=True, exist_ok=True)
        self.last_output_dir = out_dir
        modified_tnc, curves = flatten_anc_slope(
            pnc.samples,
            tnc.samples,
            tnc.sample_rate,
            start_hz,
            length_hz,
            mode,
            8192,
            2048,
            18.0,
            18.0,
        )
        end_hz = start_hz + length_hz
        output_wav = out_dir / "tnc_anc_slope_flattened.wav"
        csv_path = out_dir / "anc_slope_curve.csv"
        svg_path = out_dir / "anc_slope_curve.svg"
        report_path = out_dir / "anc_slope_report.html"
        write_wav(output_wav, modified_tnc, tnc.sample_rate)
        write_slope_curve_csv(csv_path, curves, start_hz, end_hz)
        write_slope_svg(svg_path, curves, start_hz, end_hz, "ANC slope flattening")
        write_slope_report_html(report_path, svg_path, Path(self.pnc_var.get()), Path(self.tnc_var.get()), output_wav, curves, start_hz, end_hz, mode)

        chart = {
            "type": "frequency",
            "x": curves["freq_hz"][curves["freq_hz"] <= min(max(end_hz * 2.0, end_hz + 100, 200), curves["freq_hz"][-1])],
            "band": (start_hz, end_hz),
            "series": [],
            "title": "ANC contribution slope",
        }
        visible = curves["freq_hz"] <= chart["x"][-1]
        chart["series"] = [
            ("Original ANC", curves["original_anc_db"][visible], "#d12f2f"),
            ("Target ANC", curves["target_anc_db"][visible], "#2563eb"),
            ("Modified ANC", curves["modified_anc_db"][visible], "#111827"),
        ]
        freqs = curves["freq_hz"]
        slope_rows = [
            {
                "kind": "ANC slope",
                "margin": "",
                "source": "Original ANC",
                "count": "",
                "duration": f"width={slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['effective_transition_width_hz']:.1f}Hz",
                "max_db": f"{slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['max_local_slope'] * 10:.3f}/10Hz",
                "mean_db": f"p95={slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['p95_local_slope'] * 10:.3f}/10Hz",
                "extra": f"conc={slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['concentration_ratio']:.2f}",
            },
            {
                "kind": "ANC slope",
                "margin": "",
                "source": "Modified ANC",
                "count": "",
                "duration": f"width={slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['effective_transition_width_hz']:.1f}Hz",
                "max_db": f"{slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['max_local_slope'] * 10:.3f}/10Hz",
                "mean_db": f"p95={slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['p95_local_slope'] * 10:.3f}/10Hz",
                "extra": f"conc={slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['concentration_ratio']:.2f}",
            },
        ]
        return {"mode": "slope", "output_dir": out_dir, "report": report_path, "slope_rows": slope_rows, "chart": chart}

    def make_frequency_chart(self, curves: dict, low_hz: float, high_hz: float) -> dict:
        freqs = curves["freq_hz"]
        max_freq = min(max(high_hz * 2.5, high_hz + 200, 250), float(freqs[-1]))
        mask = freqs <= max_freq
        return {
            "type": "frequency",
            "x": freqs[mask],
            "band": (low_hz, high_hz),
            "series": [
                ("OpenEar", curves["open_db"][mask], "#6b7280"),
                ("PNC", curves["pnc_db"][mask], "#2563eb"),
                ("TNC", curves["tnc_db"][mask], "#d12f2f"),
                ("Processed TNC", curves["processed_db"][mask], "#111827"),
            ],
            "title": "Spectrum overview",
        }

    def apply_result(self, result: dict) -> None:
        self.last_output_dir = result["output_dir"]
        self.last_report = result["report"]
        self.status_var.set(f"完成: {result['output_dir']}")
        self.log(f"完成。输出目录: {result['output_dir']}")
        if result.get("report"):
            self.log(f"报告: {result['report']}")

        for row in self.metrics_table.get_children():
            self.metrics_table.delete(row)
        for metric in result.get("freq", []):
            self.metrics_table.insert(
                "",
                tk.END,
                values=(
                    "frequency",
                    f"{metric.margin_db:g}",
                    f"{metric.worst_frequency_hz:.1f} Hz",
                    "",
                    "",
                    f"{metric.max_rebound_db:.2f}",
                    f"{metric.mean_positive_rebound_db:.2f}",
                    f"bins={metric.changed_stft_bins}",
                ),
            )
        for metric in result.get("time", []):
            self.metrics_table.insert(
                "",
                tk.END,
                values=(
                    "time",
                    f"{metric.margin_db:g}",
                    metric.source,
                    metric.event_count,
                    f"{metric.total_event_duration_s:.3f}s",
                    f"{metric.max_rebound_db:.2f}",
                    f"{metric.mean_positive_rebound_db:.2f}",
                    f"longest={metric.longest_event_s:.3f}s",
                ),
            )
        for row in result.get("slope_rows", []):
            self.metrics_table.insert(
                "",
                tk.END,
                values=(
                    row["kind"],
                    row["margin"],
                    row["source"],
                    row["count"],
                    row["duration"],
                    row["max_db"],
                    row["mean_db"],
                    row["extra"],
                ),
            )
        self.last_chart = result.get("chart")
        self.redraw_last_chart()

    def redraw_last_chart(self) -> None:
        if not self.last_chart:
            return
        chart = self.last_chart
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        x0, y0, x1, y1 = 70, 54, width - 24, height - 64
        self.canvas.create_text(20, 18, text=chart["title"], anchor="w", font=("Segoe UI", 13, "bold"))
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="#ffffff", outline="#d1d5db")
        x_values = np.asarray(chart["x"], dtype=float)
        if len(x_values) < 2:
            return
        all_values = np.concatenate([np.asarray(series[1], dtype=float) for series in chart["series"]])
        finite = all_values[np.isfinite(all_values)]
        if len(finite) == 0:
            return
        ymin, ymax = float(np.percentile(finite, 2)), float(np.percentile(finite, 98))
        if abs(ymax - ymin) < 1e-9:
            ymin -= 1
            ymax += 1
        pad = (ymax - ymin) * 0.1
        ymin -= pad
        ymax += pad
        xmin, xmax = float(x_values[0]), float(x_values[-1])

        if chart.get("band"):
            low, high = chart["band"]
            bx0 = x0 + (low - xmin) / max(xmax - xmin, 1e-9) * (x1 - x0)
            bx1 = x0 + (high - xmin) / max(xmax - xmin, 1e-9) * (x1 - x0)
            self.canvas.create_rectangle(bx0, y0, bx1, y1, fill="#f6c453", outline="", stipple="gray25")

        for i in range(6):
            tick = xmin + (xmax - xmin) * i / 5
            x = x0 + (tick - xmin) / max(xmax - xmin, 1e-9) * (x1 - x0)
            self.canvas.create_line(x, y1, x, y1 + 5, fill="#6b7280")
            self.canvas.create_text(x, y1 + 18, text=f"{tick:.1f}", fill="#374151", font=("Segoe UI", 9))
        for i in range(5):
            tick = ymin + (ymax - ymin) * i / 4
            y = y1 - (tick - ymin) / max(ymax - ymin, 1e-9) * (y1 - y0)
            self.canvas.create_line(x0 - 5, y, x0, y, fill="#6b7280")
            self.canvas.create_text(x0 - 8, y, text=f"{tick:.1f}", anchor="e", fill="#374151", font=("Segoe UI", 9))

        legend_x = x0 + 10
        for idx, (name, values, color) in enumerate(chart["series"]):
            y_legend = y0 + 16 + idx * 20
            self.canvas.create_line(legend_x, y_legend, legend_x + 24, y_legend, fill=color, width=2)
            self.canvas.create_text(legend_x + 30, y_legend, text=name, anchor="w", font=("Segoe UI", 9))
            values = np.asarray(values, dtype=float)
            points = []
            for x_val, y_val in zip(x_values, values):
                if not np.isfinite(y_val):
                    continue
                x = x0 + (x_val - xmin) / max(xmax - xmin, 1e-9) * (x1 - x0)
                y = y1 - (y_val - ymin) / max(ymax - ymin, 1e-9) * (y1 - y0)
                points.extend([x, y])
            if len(points) >= 4:
                self.canvas.create_line(*points, fill=color, width=2)

    def show_error(self, text: str) -> None:
        self.status_var.set("出错")
        self.log(text)
        messagebox.showerror(APP_TITLE, text[-3000:])

    def set_status(self, text: str) -> None:
        self.after(0, lambda: self.status_var.set(text))

    def log(self, text: str) -> None:
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def open_output_folder(self) -> None:
        path = self.last_output_dir or Path(self.output_dir_var.get())
        path.mkdir(parents=True, exist_ok=True)
        webbrowser.open(path.resolve().as_uri())

    def open_report(self) -> None:
        report = getattr(self, "last_report", None)
        if not report:
            messagebox.showinfo(APP_TITLE, "请先运行完整分析或时域控制。")
            return
        webbrowser.open(Path(report).resolve().as_uri())


def main() -> None:
    app = AncReboundGui()
    app.mainloop()


if __name__ == "__main__":
    main()
