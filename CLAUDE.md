# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

터치패드 센서(Sa~Sf) 6채널의 위치별 프레임간 지터(흔들림)를 시각화하는 단일 파일 GUI 도구.
`.fsd` 파일을 파싱하여 위치 맵 + 센서별 시계열 scatter plot + 통계를 표시한다.

## 실행

```bash
# Windows
run.bat
# 또는
python viewer.py

# Linux (tkinter 별도 설치 필요)
sudo apt install python3-tk
pip install pandas numpy matplotlib
python3 viewer.py

# 파일 경로를 인자로 넘길 수도 있음
python3 viewer.py data/SENSOR_point_Cal/120g_ForceLog_0415_014042.fsd
```

> `.venv/`는 Windows 전용 환경이므로 Linux에서는 시스템 Python 또는 별도 venv를 사용할 것.

## 아키텍처

`viewer.py` 단일 파일 구성:

- **`FsdParser`** — `.fsd` 파일 파싱. 첫 2줄(스케일러/헤더) 스킵 후 `(coord_x, coord_y, Sa~Sf)` 행을 읽어 연속된 동일 좌표끼리 그룹핑. `(-1, -1)` 좌표는 `baseline` 레이블로 처리.
- **`JitterViewerApp`** — tkinter 메인 GUI.
  - 좌측: matplotlib 위치 맵 (클릭으로 위치 선택)
  - 우측: 센서별 6개 subplot (3행 2열 scatter plot) + 통계 테이블
  - 하단: 슬라이더 + 좌/우 화살표 키로 위치 이동, 센서 체크박스로 표시 토글

## .fsd 파일 구조

```
<스케일러 정보>          ← line 0, 스킵
<헤더>                   ← line 1, 스킵
<frame_type>,<x>,<y>,<Sa>,<Sb>,<Sc>,<Sd>,<Se>,<Sf>,...  ← line 2~
```

동일 `(x, y)` 좌표가 연속되면 같은 위치의 여러 프레임으로 처리됨.
