"""
JitterViewer - FSD 파일 센서 지터 시각화 도구
터치패드 센서(Sa~Sf)의 각 위치별 프레임간 흔들림(jitter)을 시각화한다.
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# 센서 컬럼 목록
SENSOR_COLS = ["Sa", "Sb", "Sc", "Sd", "Se", "Sf"]
SENSOR_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]


# ─────────────────────────────────────────────
# FsdParser: .fsd 파일 파싱 클래스
# ─────────────────────────────────────────────
class FsdParser:
    """
    .fsd 파일을 파싱하여 위치 그룹별 프레임 데이터를 반환한다.
    반환 구조:
        [
          {
            "pos": (x, y),
            "label": "baseline" | "(x, y)",
            "frames": DataFrame[frame_idx, Sa, Sb, Sc, Sd, Se, Sf]
          },
          ...
        ]
    """

    def parse(self, filepath: str) -> list[dict]:
        rows = []
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 첫 줄(스케일러), 둘째 줄(헤더) 건너뜀
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 9:
                continue
            try:
                coord_x = int(parts[1])
                coord_y = int(parts[2])
                sa = int(parts[3])
                sb = int(parts[4])
                sc = int(parts[5])
                sd = int(parts[6])
                se = int(parts[7])
                sf = int(parts[8])
            except ValueError:
                continue
            rows.append((coord_x, coord_y, sa, sb, sc, sd, se, sf))

        if not rows:
            return []

        # (coord_x, coord_y) 기준으로 연속된 행들을 그룹핑
        groups = []
        prev_pos = None
        current_frames = []

        for row in rows:
            pos = (row[0], row[1])
            if pos != prev_pos:
                if prev_pos is not None:
                    groups.append(self._build_group(prev_pos, current_frames))
                prev_pos = pos
                current_frames = [row[2:]]
            else:
                current_frames.append(row[2:])

        if prev_pos is not None:
            groups.append(self._build_group(prev_pos, current_frames))

        return groups

    def _build_group(self, pos: tuple, frame_rows: list) -> dict:
        df = pd.DataFrame(frame_rows, columns=SENSOR_COLS)
        df.insert(0, "frame_idx", range(len(df)))

        if pos == (-1, -1):
            label = "baseline"
        else:
            label = f"({pos[0]}, {pos[1]})"

        return {"pos": pos, "label": label, "frames": df}


# ─────────────────────────────────────────────
# JitterViewerApp: tkinter GUI 메인 클래스
# ─────────────────────────────────────────────
class JitterViewerApp:
    def __init__(self, root: tk.Tk, initial_file: str = None):
        self.root = root
        self.root.title("JitterViewer")
        self.root.geometry("1300x750")
        self.root.minsize(900, 600)

        self.parser = FsdParser()
        self.groups: list[dict] = []
        self.current_idx: int = 0
        self.filepath: str = ""

        # 센서 체크박스 상태
        self.sensor_vars: dict[str, tk.BooleanVar] = {
            s: tk.BooleanVar(value=True) for s in SENSOR_COLS
        }

        self._build_ui()
        self._bind_keys()

        if initial_file and os.path.isfile(initial_file):
            self._load_file(initial_file)

    # ── UI 구성 ─────────────────────────────
    def _build_ui(self):
        # 상단 툴바
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED, pady=4)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="파일 선택", command=self._on_open_file).pack(side=tk.LEFT, padx=6)
        self.lbl_file = tk.Label(toolbar, text="파일을 선택하세요.", anchor="w", fg="#555")
        self.lbl_file.pack(side=tk.LEFT, padx=4)

        # 메인 영역 (좌: 맵, 우: 그래프)
        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ── 좌측 패널: 좌표 맵 ──
        left_panel = tk.Frame(main_frame, width=380, bd=1, relief=tk.SUNKEN)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=4, pady=4)
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="위치 맵", font=("", 10, "bold")).pack(pady=(4, 0))

        self.map_fig = Figure(figsize=(3.6, 4.0), dpi=96)
        self.map_ax = self.map_fig.add_subplot(111)
        self.map_canvas = FigureCanvasTkAgg(self.map_fig, master=left_panel)
        self.map_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.map_canvas.mpl_connect("button_press_event", self._on_map_click)

        # ── 우측 패널: 시계열 그래프 + 통계 ──
        right_panel = tk.Frame(main_frame, bd=1, relief=tk.SUNKEN)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.graph_fig = Figure(figsize=(7, 5.5), dpi=96)
        # 6개 센서를 2열 3행 subplot으로 구성
        self.graph_axes = []
        for i in range(6):
            ax = self.graph_fig.add_subplot(3, 2, i + 1)
            self.graph_axes.append(ax)
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=right_panel)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 통계 패널
        self.stat_frame = tk.Frame(right_panel, bd=1, relief=tk.GROOVE)
        self.stat_frame.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(self.stat_frame, text="통계", font=("", 9, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=4
        )
        headers = ["센서", "평균(mean)", "표준편차(std)", "범위(range)"]
        for col, h in enumerate(headers):
            tk.Label(self.stat_frame, text=h, font=("", 8, "bold"), width=14).grid(
                row=1, column=col, padx=2
            )
        self.stat_labels: dict[str, list[tk.Label]] = {}
        for i, sensor in enumerate(SENSOR_COLS):
            row_idx = i + 2
            tk.Label(self.stat_frame, text=sensor, font=("", 8), fg=SENSOR_COLORS[i]).grid(
                row=row_idx, column=0, padx=2, sticky="w"
            )
            labels = []
            for col in range(1, 4):
                lbl = tk.Label(self.stat_frame, text="-", font=("", 8), width=14)
                lbl.grid(row=row_idx, column=col, padx=2)
                labels.append(lbl)
            self.stat_labels[sensor] = labels

        # ── 하단: 슬라이더 + 체크박스 ──
        bottom_frame = tk.Frame(self.root, bd=1, relief=tk.RAISED, pady=4)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 슬라이더
        slider_frame = tk.Frame(bottom_frame)
        slider_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(slider_frame, text="위치 이동:").pack(side=tk.LEFT)
        self.slider_var = tk.IntVar(value=0)
        self.slider = tk.Scale(
            slider_frame,
            variable=self.slider_var,
            from_=0, to=0,
            orient=tk.HORIZONTAL,
            length=250,
            command=self._on_slider_change,
        )
        self.slider.pack(side=tk.LEFT)
        self.lbl_pos = tk.Label(slider_frame, text="위치: -", width=20, anchor="w")
        self.lbl_pos.pack(side=tk.LEFT, padx=4)

        # 센서 체크박스
        cb_frame = tk.LabelFrame(bottom_frame, text="센서 선택", padx=4, pady=2)
        cb_frame.pack(side=tk.LEFT, padx=12)
        for i, sensor in enumerate(SENSOR_COLS):
            cb = tk.Checkbutton(
                cb_frame,
                text=sensor,
                variable=self.sensor_vars[sensor],
                fg=SENSOR_COLORS[i],
                command=self._refresh_graph,
            )
            cb.pack(side=tk.LEFT)

    def _bind_keys(self):
        self.root.bind("<Left>", lambda e: self._move_position(-1))
        self.root.bind("<Right>", lambda e: self._move_position(1))

    # ── 파일 열기 ─────────────────────────────
    def _on_open_file(self):
        path = filedialog.askopenfilename(
            title="FSD 파일 선택",
            filetypes=[("FSD files", "*.fsd"), ("All files", "*.*")],
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        try:
            self.groups = self.parser.parse(path)
        except Exception as e:
            tk.messagebox.showerror("오류", f"파일 파싱 실패:\n{e}")
            return

        self.filepath = path
        self.lbl_file.config(text=os.path.basename(path))
        self.current_idx = 0

        # 슬라이더 범위 업데이트
        n = max(len(self.groups) - 1, 0)
        self.slider.config(from_=0, to=n)
        self.slider_var.set(0)

        self._refresh_map()
        self._refresh_graph()

    # ── 위치 이동 ─────────────────────────────
    def _move_position(self, delta: int):
        if not self.groups:
            return
        new_idx = max(0, min(len(self.groups) - 1, self.current_idx + delta))
        if new_idx != self.current_idx:
            self.current_idx = new_idx
            self.slider_var.set(new_idx)
            self._refresh_map()
            self._refresh_graph()

    def _on_slider_change(self, val):
        idx = int(float(val))
        if idx != self.current_idx:
            self.current_idx = idx
            self._refresh_map()
            self._refresh_graph()

    # ── 맵 클릭 처리 ─────────────────────────
    def _on_map_click(self, event):
        if not self.groups or event.inaxes != self.map_ax:
            return

        # baseline 제외한 실제 좌표 포인트들
        real_groups = [
            (i, g) for i, g in enumerate(self.groups) if g["pos"] != (-1, -1)
        ]
        if not real_groups:
            return

        click_x, click_y = event.xdata, event.ydata
        min_dist = float("inf")
        best_idx = self.current_idx

        for i, g in real_groups:
            px, py = g["pos"]
            dist = (px - click_x) ** 2 + (py - click_y) ** 2
            if dist < min_dist:
                min_dist = dist
                best_idx = i

        if best_idx != self.current_idx:
            self.current_idx = best_idx
            self.slider_var.set(best_idx)
            self._refresh_map()
            self._refresh_graph()

    # ── 맵 렌더링 ─────────────────────────────
    def _refresh_map(self):
        ax = self.map_ax
        ax.clear()

        real_groups = [(i, g) for i, g in enumerate(self.groups) if g["pos"] != (-1, -1)]
        if not real_groups:
            self.map_canvas.draw()
            return

        xs = [g["pos"][0] for _, g in real_groups]
        ys = [g["pos"][1] for _, g in real_groups]

        # 전체 포인트 (회색)
        ax.scatter(xs, ys, c="#aaaaaa", s=40, zorder=2, picker=5)

        # 현재 선택 포인트 강조
        cur_group = self.groups[self.current_idx]
        if cur_group["pos"] != (-1, -1):
            cx, cy = cur_group["pos"]
            ax.scatter([cx], [cy], c="#e74c3c", s=120, zorder=3, edgecolors="black", linewidths=1.0)

        ax.set_xlabel("coord_x", fontsize=8)
        ax.set_ylabel("coord_y", fontsize=8)
        ax.set_title("위치 맵", fontsize=9)
        ax.tick_params(labelsize=7)
        self.map_fig.tight_layout()
        self.map_canvas.draw()

    # ── 그래프 렌더링 ─────────────────────────
    def _refresh_graph(self):
        for ax in self.graph_axes:
            ax.clear()

        if not self.groups:
            self.graph_canvas.draw()
            return

        group = self.groups[self.current_idx]
        df = group["frames"]
        label = group["label"]
        fname = os.path.basename(self.filepath) if self.filepath else ""

        # 센서별로 개별 subplot에 점(scatter)으로 표시
        for i, sensor in enumerate(SENSOR_COLS):
            ax = self.graph_axes[i]
            visible = self.sensor_vars[sensor].get()
            if visible:
                ax.scatter(
                    df["frame_idx"],
                    df[sensor],
                    color=SENSOR_COLORS[i],
                    s=12,
                    zorder=2,
                )
            ax.set_title(sensor, fontsize=8, color=SENSOR_COLORS[i], fontweight="bold")
            ax.set_xlabel("frame", fontsize=7)
            ax.set_ylabel("value (u16)", fontsize=7)
            ax.tick_params(labelsize=6)
            ax.grid(True, alpha=0.3)

        # 전체 제목 (suptitle)
        self.graph_fig.suptitle(
            f"{fname}  |  위치: {label}", fontsize=8, y=1.01
        )
        self.graph_fig.tight_layout()
        self.graph_canvas.draw()

        # 통계 업데이트
        self._refresh_stats(df)
        # 위치 레이블 업데이트
        self.lbl_pos.config(text=f"위치: {label}")

    # ── 통계 패널 업데이트 ───────────────────
    def _refresh_stats(self, df: pd.DataFrame):
        for sensor in SENSOR_COLS:
            vals = df[sensor]
            mean_val = vals.mean()
            std_val = vals.std()
            range_val = vals.max() - vals.min()
            labels = self.stat_labels[sensor]
            labels[0].config(text=f"{mean_val:.2f}")
            labels[1].config(text=f"{std_val:.4f}")
            labels[2].config(text=f"{range_val}")


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # 커맨드라인 인자로 파일 경로 선택적 지원
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None

    root = tk.Tk()
    app = JitterViewerApp(root, initial_file=initial_file)
    root.mainloop()
