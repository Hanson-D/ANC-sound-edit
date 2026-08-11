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
from typing import List, Tuple
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
from audio_band_limiter import read_wav, simplify_curve, spectrum_curve, write_wav


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
        self.slope_mode_var = tk.StringVar(value="平缓")
        self.slope_start_reduction_var = tk.StringVar(value="0")
        self.slope_end_reduction_var = tk.StringVar(value="0")
        self.slope_start_transition_var = tk.StringVar(value="0")
        self.slope_end_transition_var = tk.StringVar(value="0")
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
        controls.rowconfigure(1, weight=1)

        files = ttk.LabelFrame(controls, text="音频文件", padding=10)
        files.grid(row=0, column=0, columnspan=3, sticky="ew")
        files.columnconfigure(1, weight=1)
        self._file_row(files, 0, "开耳 OpenEar", self.open_ear_var)
        self._file_row(files, 1, "被动 PNC", self.pnc_var)
        self._file_row(files, 2, "总降噪 TNC", self.tnc_var)

        task_tabs = ttk.Notebook(controls)
        task_tabs.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(12, 0))

        analysis = ttk.Frame(task_tabs, padding=10)
        control = ttk.Frame(task_tabs, padding=10)
        slope = ttk.Frame(task_tabs, padding=10)
        output = ttk.Frame(task_tabs, padding=10)
        task_tabs.add(analysis, text="完整分析")
        task_tabs.add(control, text="时域控制")
        task_tabs.add(slope, text="斜率平滑")
        task_tabs.add(output, text="输出")

        for frame in (analysis, control, slope, output):
            for col in range(4):
                frame.columnconfigure(col, weight=1)

        self._section_note(
            analysis,
            0,
            "用途：同时分析频域反弹、时域反弹次数，并生成多个频域限幅后的 TNC 版本。需要 OpenEar、PNC、TNC。",
        )
        self._entry(analysis, 1, 0, "低频起点 Hz", self.low_hz_var)
        self._entry(analysis, 1, 2, "低频终点 Hz", self.high_hz_var)
        self._entry(analysis, 2, 0, "Margin 列表 dB", self.margins_var)
        self._entry(analysis, 3, 0, "时间窗 ms", self.time_window_var)
        self._entry(analysis, 3, 2, "步长 ms", self.time_hop_var)
        self._entry(analysis, 4, 0, "最短事件 ms", self.min_event_var)
        self._entry(analysis, 4, 2, "合并间隔 ms", self.merge_gap_var)
        ttk.Button(analysis, text="运行完整分析", command=self.run_full_analysis).grid(
            row=5, column=0, columnspan=4, sticky="ew", pady=(12, 0)
        )
        self._help_table(
            analysis,
            6,
            [
                ("低频起点/终点 Hz", "定义要观察和处理的反弹频段。低频反弹通常看 0-100 Hz；对数图从 1 Hz 起显示。"),
                ("Margin 列表 dB", "判断反弹的容忍余量。0 表示 TNC 只要高于 PNC 就算反弹；1,3 表示允许高出 1/3 dB。可填 0,1,3。"),
                ("时间窗 ms", "时域反弹统计的 RMS 窗长。低频建议 200 ms 左右，太短会让 0-100 Hz 的 RMS 不稳定。"),
                ("步长 ms", "RMS 窗口移动间隔。25 ms 可较细地定位事件时间。"),
                ("最短事件 ms", "短于该时长的超限片段不计为一次反弹，避免把瞬时抖动算进去。"),
                ("合并间隔 ms", "两段反弹中间间隔小于该值时合并为同一次事件。"),
            ],
        )

        self._section_note(
            control,
            0,
            "用途：PNC 不动，只对 TNC 的目标低频带做时域包络控制，减少反弹次数。需要 PNC、TNC。",
        )
        self._entry(control, 1, 0, "低频起点 Hz", self.low_hz_var)
        self._entry(control, 1, 2, "低频终点 Hz", self.high_hz_var)
        self._entry(control, 2, 0, "控制 Margin dB", self.margin_var)
        self._entry(control, 2, 2, "Safety dB", self.safety_var)
        self._entry(control, 3, 0, "时间窗 ms", self.time_window_var)
        self._entry(control, 3, 2, "步长 ms", self.time_hop_var)
        self._entry(control, 4, 0, "Attack ms", self.attack_var)
        self._entry(control, 4, 2, "Release ms", self.release_var)
        self._entry(control, 5, 0, "最短事件 ms", self.min_event_var)
        self._entry(control, 5, 2, "合并间隔 ms", self.merge_gap_var)
        self._entry(control, 6, 0, "最大衰减 dB", self.max_atten_var)
        ttk.Button(control, text="运行时域反弹控制", command=self.run_time_control).grid(
            row=7, column=0, columnspan=4, sticky="ew", pady=(12, 0)
        )
        self._help_table(
            control,
            8,
            [
                ("低频起点/终点 Hz", "只控制这个频段内的 TNC 低频分量；频段外残差信号保持不动。"),
                ("控制 Margin dB", "控制目标为 TNC 目标频段 RMS 不高于 PNC + Margin。0 表示尽量压到不高于 PNC。"),
                ("Safety dB", "额外安全余量。设为 1 表示目标压到 PNC + Margin - 1 dB，更容易减少事件次数。"),
                ("时间窗/步长 ms", "用于检测时域反弹事件，也用于生成控制包络。默认 200/25 ms。"),
                ("Attack ms", "反弹出现时增益压低的速度。越小越快，事件更少，但更可能产生包络痕迹。"),
                ("Release ms", "反弹结束后增益恢复速度。越大越平滑，越小越激进。"),
                ("最大衰减 dB", "限制最多压低多少 dB，避免处理过猛。"),
                ("最短事件/合并间隔 ms", "用于控制前后事件数量统计，定义同完整分析。"),
            ],
        )

        self._section_note(
            slope,
            0,
            "用途：按频率定义 ANC=PNC(dB)-TNC(dB)，重塑选定频段内的 ANC 降噪量斜率。需要 PNC、TNC。",
        )
        self._entry(slope, 1, 0, "起始频率 Hz", self.slope_start_var)
        self._entry(slope, 1, 2, "替代长度 Hz", self.slope_length_var)
        self._entry(slope, 2, 0, "起点压浅 dB", self.slope_start_reduction_var)
        self._entry(slope, 2, 2, "终点压浅 dB", self.slope_end_reduction_var)
        self._entry(slope, 3, 0, "起点过渡 Hz", self.slope_start_transition_var)
        self._entry(slope, 3, 2, "终点过渡 Hz", self.slope_end_transition_var)
        ttk.Label(slope, text="平滑模式").grid(row=4, column=0, sticky="w", pady=4, padx=(0, 6))
        ttk.Combobox(
            slope,
            textvariable=self.slope_mode_var,
            values=("平缓", "线性"),
            width=9,
            state="readonly",
        ).grid(row=4, column=1, sticky="ew", pady=4)
        ttk.Button(slope, text="运行 ANC 斜率平滑", command=self.run_slope_flattening).grid(
            row=5, column=0, columnspan=4, sticky="ew", pady=(12, 0)
        )
        self._help_table(
            slope,
            6,
            [
                ("起始频率 Hz", "要替换的 ANC 降噪量曲线片段起点。计算仍用 ANC=PNC(dB)-TNC(dB)，界面显示为负值降噪。"),
                ("替代长度 Hz", "从起始频率往后的替代宽度。例如起始 30、长度 50 表示替换 30-80 Hz。"),
                ("起点/终点压浅 dB", "先把端点 ANC 深度减少指定 dB，再做平滑。起点填 3 表示起点先少 3 dB 降噪深度，会改变整体斜率。"),
                ("起点/终点过渡 Hz", "在主替代段前后增加平滑接入/接出宽度，避免端点压浅造成突变。0 表示不加额外过渡。"),
                ("平滑模式", "平缓：首尾更顺，默认建议；线性：端点之间直线过渡。"),
                ("输出 WAV", "PNC 不动，通过缩放 TNC 频谱幅度生成新的 TNC，用来让 ANC 曲线在该段更平缓。"),
                ("斜率指标", "重点看最大局部斜率、P95 局部斜率、有效宽度和集中度；平均斜率受端点约束，不是主要判断。"),
            ],
        )

        self._dir_row(output, 0, "输出目录", self.output_dir_var)
        ttk.Button(output, text="打开输出文件夹", command=self.open_output_folder).grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=(12, 0)
        )
        ttk.Button(output, text="打开 HTML 报告", command=self.open_report).grid(
            row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0)
        )
        ttk.Label(output, text="当前状态").grid(row=3, column=0, sticky="w", pady=(14, 0))
        ttk.Label(output, textvariable=self.status_var, wraplength=310).grid(
            row=4, column=0, columnspan=4, sticky="ew", pady=(4, 0)
        )
        self._help_table(
            output,
            5,
            [
                ("输出目录", "每个任务会在该目录下创建独立子目录，例如 full_analysis、time_control、slope_flattening。"),
                ("HTML 报告", "包含图、指标表和输出文件路径，适合保存或发给同事查看。"),
                ("CSV 文件", "保存逐频点或逐时间窗数据，适合后续统计和画图。"),
                ("WAV 文件", "处理后的 TNC 音频，用于主观听感或对比实验。"),
            ],
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
            "margin": "余量",
            "source": "来源/频点",
            "count": "次数",
            "duration": "持续时间",
            "max_db": "峰值/最大",
            "mean_db": "平均/P95",
            "extra": "补充",
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
        ttk.Button(parent, text="选择", command=lambda: self.pick_file(var)).grid(row=row, column=2, padx=(6, 0), pady=3)

    def _dir_row(self, parent, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var, width=34).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(parent, text="选择", command=lambda: self.pick_dir(var)).grid(row=row, column=2, padx=(6, 0), pady=3)

    def _entry(self, parent, row: int, col: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=4, padx=(0, 6))
        ttk.Entry(parent, textvariable=var, width=11).grid(row=row, column=col + 1, sticky="ew", pady=4)

    def _section_note(self, parent, row: int, text: str) -> None:
        ttk.Label(parent, text=text, wraplength=330, foreground="#374151").grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=(0, 10)
        )

    def _help_table(self, parent, row: int, items: List[Tuple[str, str]]) -> None:
        frame = ttk.LabelFrame(parent, text="参数定义与作用", padding=8)
        frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        frame.columnconfigure(1, weight=1)
        for index, (name, description) in enumerate(items):
            ttk.Label(frame, text=name, width=16).grid(row=index, column=0, sticky="nw", pady=3, padx=(0, 8))
            ttk.Label(frame, text=description, wraplength=285, foreground="#374151").grid(
                row=index, column=1, sticky="ew", pady=3
            )

    def pick_file(self, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename(filetypes=[("WAV 音频文件", "*.wav *.WAV"), ("所有文件", "*.*")])
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
            raise ValueError("Margin 列表不能为空")

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

        rms_chart = {
            "type": "time",
            "x": frame_times_s,
            "x_scale": "linear",
            "x_label": "时间 (s)",
            "y_label": "目标频段 RMS / 增益 (dB)",
            "description": "可视化对象：PNC、原始TNC、控制后TNC 的目标频段短窗RMS，以及施加到TNC目标频段的增益。",
            "series": [
                ("PNC", pnc_rms_db, "#2563eb"),
                ("原始 TNC", tnc_rms_db, "#d12f2f"),
                ("控制后 TNC", controlled_rms_db, "#111827"),
                ("施加增益 dB", applied_gain_db, "#0f766e"),
            ],
            "title": "目标频段 RMS 与控制增益",
        }
        spectrum_chart = self.make_time_control_spectrum_chart(pnc.samples, tnc.samples, controlled, tnc.sample_rate)
        chart = {
            "type": "panels",
            "title": "时域控制结果",
            "description": "上图显示时域反弹控制过程；下图显示控制前后的整体对数频谱。",
            "panels": [rms_chart, spectrum_chart],
        }
        return {"mode": "control", "output_dir": out_dir, "report": report_path, "time": time_metrics, "chart": chart}

    def _run_slope_flattening(self) -> dict:
        params = self.read_common_params()
        start_hz = float(self.slope_start_var.get())
        length_hz = float(self.slope_length_var.get())
        start_depth_reduction_db = float(self.slope_start_reduction_var.get())
        end_depth_reduction_db = float(self.slope_end_reduction_var.get())
        start_transition_hz = float(self.slope_start_transition_var.get())
        end_transition_hz = float(self.slope_end_transition_var.get())
        mode_label = self.slope_mode_var.get()
        mode = self.slope_mode_value()
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
            start_depth_reduction_db,
            end_depth_reduction_db,
            start_transition_hz,
            end_transition_hz,
        )
        end_hz = start_hz + length_hz
        output_wav = out_dir / "tnc_anc_slope_flattened.wav"
        csv_path = out_dir / "anc_slope_curve.csv"
        svg_path = out_dir / "anc_slope_curve.svg"
        report_path = out_dir / "anc_slope_report.html"
        write_wav(output_wav, modified_tnc, tnc.sample_rate)
        write_slope_curve_csv(csv_path, curves, start_hz, end_hz, start_transition_hz, end_transition_hz)
        write_slope_svg(svg_path, curves, start_hz, end_hz, "ANC slope flattening")
        write_slope_report_html(
            report_path,
            svg_path,
            Path(self.pnc_var.get()),
            Path(self.tnc_var.get()),
            output_wav,
            curves,
            start_hz,
            end_hz,
            mode,
            start_depth_reduction_db,
            end_depth_reduction_db,
            start_transition_hz,
            end_transition_hz,
        )

        chart = {
            "type": "frequency",
            "x": curves["freq_hz"][curves["freq_hz"] <= min(max(end_hz * 2.0, end_hz + 100, 200), curves["freq_hz"][-1])],
            "x_range": (1.0, max(end_hz * 2.0, end_hz + 100, 200)),
            "x_scale": "log",
            "x_label": "频率 (Hz，对数坐标)",
            "y_label": "ANC 显示值 (dB，降噪为负)",
            "description": f"可视化对象：ANC降噪量曲线。界面显示为负值降噪。端点压浅：起点 {start_depth_reduction_db:g} dB，终点 {end_depth_reduction_db:g} dB；过渡：起点 {start_transition_hz:g} Hz，终点 {end_transition_hz:g} Hz。",
            "band": (start_hz, end_hz),
            "series": [],
            "title": "ANC 降噪量斜率",
        }
        visible = curves["freq_hz"] <= chart["x"][-1]
        chart["series"] = [
            ("原始 ANC", -curves["original_anc_db"][visible], "#d12f2f"),
            ("目标 ANC", -curves["target_anc_db"][visible], "#2563eb"),
            ("修改后 ANC", -curves["modified_anc_db"][visible], "#111827"),
        ]
        freqs = curves["freq_hz"]
        slope_rows = [
            {
                "kind": "ANC 斜率",
                "margin": "",
                "source": "原始 ANC",
                "count": "",
                "duration": f"有效宽度={slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['effective_transition_width_hz']:.1f}Hz",
                "max_db": f"{slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['max_local_slope'] * 10:.3f}/10Hz",
                "mean_db": f"p95={slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['p95_local_slope'] * 10:.3f}/10Hz",
                "extra": f"集中度={slope_shape_metrics(freqs, curves['original_anc_db'], start_hz, end_hz)['concentration_ratio']:.2f}",
            },
            {
                "kind": "ANC 斜率",
                "margin": "",
                "source": "修改后 ANC",
                "count": "",
                "duration": f"有效宽度={slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['effective_transition_width_hz']:.1f}Hz",
                "max_db": f"{slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['max_local_slope'] * 10:.3f}/10Hz",
                "mean_db": f"p95={slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['p95_local_slope'] * 10:.3f}/10Hz",
                "extra": f"集中度={slope_shape_metrics(freqs, curves['modified_anc_db'], start_hz, end_hz)['concentration_ratio']:.2f}; {mode_label}",
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
            "x_range": (1.0, max(high_hz * 2.5, high_hz + 200, 250)),
            "x_scale": "log",
            "x_label": "频率 (Hz，对数坐标)",
            "y_label": "幅度 (dB)",
            "description": "可视化对象：OpenEar、PNC、原始TNC、处理后TNC 的频谱幅度曲线。",
            "band": (low_hz, high_hz),
            "series": [
                ("OpenEar", curves["open_db"][mask], "#6b7280"),
                ("PNC", curves["pnc_db"][mask], "#2563eb"),
                ("TNC", curves["tnc_db"][mask], "#d12f2f"),
                ("处理后 TNC", curves["processed_db"][mask], "#111827"),
            ],
            "title": "频谱概览",
        }

    def make_time_control_spectrum_chart(
        self,
        pnc_samples: np.ndarray,
        tnc_samples: np.ndarray,
        controlled_samples: np.ndarray,
        sample_rate: int,
    ) -> dict:
        min_len = min(len(pnc_samples), len(tnc_samples), len(controlled_samples))
        freqs, pnc_db, _ = spectrum_curve(pnc_samples[:min_len], sample_rate)
        _, tnc_db, _ = spectrum_curve(tnc_samples[:min_len], sample_rate)
        _, controlled_db, _ = spectrum_curve(controlled_samples[:min_len], sample_rate)
        max_freq = float(freqs[-1])
        visible = freqs > 0
        x_values, pnc_values = simplify_curve(freqs[visible], pnc_db[visible])
        _, tnc_values = simplify_curve(freqs[visible], tnc_db[visible])
        _, controlled_values = simplify_curve(freqs[visible], controlled_db[visible])
        return {
            "type": "frequency",
            "x": x_values,
            "x_range": (1.0, max_freq),
            "x_scale": "log",
            "x_label": "频率 (Hz，对数坐标)",
            "y_label": "幅度 (dB)",
            "description": "可视化对象：PNC、原始TNC、时域控制后TNC 的整体频谱幅度曲线。",
            "series": [
                ("PNC", pnc_values, "#2563eb"),
                ("原始 TNC", tnc_values, "#d12f2f"),
                ("控制后 TNC", controlled_values, "#111827"),
            ],
            "title": "整体频谱对比",
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
                    "频域",
                    f"{metric.margin_db:g}",
                    f"{metric.worst_frequency_hz:.1f} Hz",
                    "",
                    "",
                    f"{metric.max_rebound_db:.2f}",
                    f"{metric.mean_positive_rebound_db:.2f}",
                    f"改变bin={metric.changed_stft_bins}",
                ),
            )
        for metric in result.get("time", []):
            self.metrics_table.insert(
                "",
                tk.END,
                values=(
                    "时域",
                    f"{metric.margin_db:g}",
                    self.display_source_name(metric.source),
                    metric.event_count,
                    f"{metric.total_event_duration_s:.3f}s",
                    f"{metric.max_rebound_db:.2f}",
                    f"{metric.mean_positive_rebound_db:.2f}",
                    f"最长={metric.longest_event_s:.3f}s",
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

    def display_source_name(self, value: str) -> str:
        names = {
            "original_tnc": "原始 TNC",
            "processed_tnc": "处理后 TNC",
        }
        return names.get(value, value)

    def slope_mode_value(self) -> str:
        values = {
            "平缓": "smoothstep",
            "线性": "linear",
            "smoothstep": "smoothstep",
            "linear": "linear",
        }
        return values.get(self.slope_mode_var.get(), "smoothstep")

    def redraw_last_chart(self) -> None:
        if not self.last_chart:
            return
        chart = self.last_chart
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)

        if chart.get("type") == "panels":
            self.canvas.create_text(20, 18, text=chart["title"], anchor="w", font=("Segoe UI", 13, "bold"))
            self.canvas.create_text(
                20,
                42,
                text=chart.get("description", ""),
                anchor="w",
                fill="#4b5563",
                font=("Segoe UI", 9),
            )
            panels = chart.get("panels", [])
            if not panels:
                return
            top_margin = 112
            bottom_margin = 58
            gap = 58
            available_height = height - top_margin - bottom_margin - gap * (len(panels) - 1)
            panel_height = max(120, available_height / len(panels))
            for index, panel in enumerate(panels):
                panel_y0 = top_margin + index * (panel_height + gap)
                panel_y1 = panel_y0 + panel_height
                if panel_y1 - panel_y0 < 80:
                    continue
                self.draw_chart_panel(panel, 84, panel_y0, width - 24, panel_y1)
            return

        self.draw_chart_panel(chart, 84, 76, width - 24, height - 76, header_x=20, title_y=18, description_y=42)

    def draw_chart_panel(
        self,
        chart: dict,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        header_x: float | None = None,
        title_y: float | None = None,
        description_y: float | None = None,
    ) -> None:
        header_x = x0 if header_x is None else header_x
        title_y = y0 - 42 if title_y is None else title_y
        description_y = y0 - 20 if description_y is None else description_y
        self.canvas.create_text(header_x, title_y, text=chart["title"], anchor="w", font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(
            header_x,
            description_y,
            text=chart.get("description", ""),
            anchor="w",
            fill="#4b5563",
            font=("Segoe UI", 9),
        )
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
        x_scale = chart.get("x_scale", "linear")
        if "x_range" in chart:
            xmin, xmax = chart["x_range"]
        else:
            xmin, xmax = float(x_values[0]), float(x_values[-1])
        data_xmin, data_xmax = float(x_values[0]), float(x_values[-1])
        if x_scale == "log":
            positive_x = x_values[x_values > 0]
            if len(positive_x) == 0:
                return
            xmin = max(float(xmin), min(1.0, float(np.min(positive_x))))
            xmax = max(float(xmax), xmin * 10.0)
        if xmax <= xmin:
            xmax = xmin + 1.0

        def x_to_px(value: float) -> float:
            if x_scale == "log":
                safe_value = max(value, xmin)
                return x0 + (np.log10(safe_value) - np.log10(xmin)) / max(np.log10(xmax) - np.log10(xmin), 1e-9) * (x1 - x0)
            return x0 + (value - xmin) / max(xmax - xmin, 1e-9) * (x1 - x0)

        if chart.get("band"):
            low, high = chart["band"]
            bx0 = x_to_px(max(low, xmin))
            bx1 = x_to_px(max(high, xmin))
            self.canvas.create_rectangle(bx0, y0, bx1, y1, fill="#f6c453", outline="", stipple="gray25")

        for tick in self.x_ticks(xmin, xmax, x_scale):
            x = x_to_px(tick)
            self.canvas.create_line(x, y1, x, y1 + 5, fill="#6b7280")
            self.canvas.create_text(x, y1 + 18, text=self.format_tick(tick), fill="#374151", font=("Segoe UI", 9))
        for i in range(5):
            tick = ymin + (ymax - ymin) * i / 4
            y = y1 - (tick - ymin) / max(ymax - ymin, 1e-9) * (y1 - y0)
            self.canvas.create_line(x0 - 5, y, x0, y, fill="#6b7280")
            self.canvas.create_text(x0 - 8, y, text=f"{tick:.1f}", anchor="e", fill="#374151", font=("Segoe UI", 9))
        self.canvas.create_text((x0 + x1) / 2, y1 + 42, text=chart.get("x_label", ""), fill="#111827", font=("Segoe UI", 10))
        self.canvas.create_text(
            x0 - 66,
            (y0 + y1) / 2,
            text=chart.get("y_label", ""),
            angle=90,
            fill="#111827",
            font=("Segoe UI", 10),
        )

        legend_x = x0 + 10
        for idx, (name, values, color) in enumerate(chart["series"]):
            y_legend = y0 + 16 + idx * 20
            self.canvas.create_line(legend_x, y_legend, legend_x + 24, y_legend, fill=color, width=2)
            self.canvas.create_text(legend_x + 30, y_legend, text=name, anchor="w", font=("Segoe UI", 9))
            values = np.asarray(values, dtype=float)
            points = []
            for x_val, y_val in zip(x_values, values):
                if not np.isfinite(y_val) or x_val < xmin or x_val > xmax or (x_scale == "log" and x_val <= 0):
                    continue
                x = x_to_px(float(x_val))
                y = y1 - (y_val - ymin) / max(ymax - ymin, 1e-9) * (y1 - y0)
                points.extend([x, y])
            if len(points) >= 4:
                self.canvas.create_line(*points, fill=color, width=2)

    def x_ticks(self, xmin: float, xmax: float, scale: str) -> List[float]:
        if scale != "log":
            return [xmin + (xmax - xmin) * i / 5 for i in range(6)]
        ticks = []
        start_power = int(np.floor(np.log10(max(xmin, 1e-9))))
        end_power = int(np.ceil(np.log10(max(xmax, xmin * 10))))
        for power in range(start_power, end_power + 1):
            for multiplier in (1, 2, 5):
                value = multiplier * (10 ** power)
                if xmin <= value <= xmax:
                    ticks.append(float(value))
        return ticks

    def format_tick(self, value: float) -> str:
        if value >= 1000:
            return f"{value / 1000:g}k"
        if value >= 10:
            return f"{value:.0f}"
        return f"{value:g}"

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
