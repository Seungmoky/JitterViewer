# JitterViewer

터치패드 센서(Sa~Sf) 6채널의 위치별 프레임간 지터(흔들림)를 시각화하는 GUI 도구.

## 기능

- `.fsd` 파일 파싱 및 위치별 프레임 그룹핑
- 좌측 위치 맵: 클릭으로 측정 위치 선택
- 우측 센서별 scatter plot (3행 2열, Sa~Sf)
- 통계 테이블: 센서별 평균 / 표준편차 / 범위
- 하단 슬라이더 및 좌우 방향키로 위치 순차 이동
- 센서 체크박스로 개별 표시/숨김

## 실행

```bash
# Windows
run.bat

# Linux (tkinter 미설치 시 별도 설치 필요)
sudo apt install python3-tk
pip install pandas numpy matplotlib
python3 viewer.py

# 파일 경로를 인자로 직접 지정
python3 viewer.py data/SENSOR_point_Cal/120g_ForceLog_0415_014042.fsd
```

## 사용법

1. `viewer.py` 실행
2. 좌측 상단 **파일 선택** 버튼 클릭 → `.fsd` 파일 선택 (`data/` 폴더에서 시작)
3. 좌측 위치 맵에서 점 클릭 또는 하단 슬라이더로 위치 이동
   - 방향키(←→)로도 인덱스 순서대로 이동 가능
   - baseline(-1, -1) 포함 전체 위치 순회 가능
4. 우측 그래프에서 센서별 지터 확인, 통계 테이블로 수치 검토
5. 좌표가 맞지 않을 경우 `.fsd` 파일을 직접 열어 좌표/순서 수정 후 재검토

## 프로젝트 구조

```
jitterViewer/
├── viewer.py          # 메인 GUI (FsdParser + JitterViewerApp)
├── run.bat            # Windows 실행 스크립트
├── data/              # 샘플 .fsd 테스트 데이터
│   └── SENSOR_point_Cal/
└── README.md
```

## .fsd 파일 구조

```
<스케일러 정보>          ← line 0, 스킵
<헤더>                   ← line 1, 스킵
<frame_type>,<x>,<y>,<Sa>,<Sb>,<Sc>,<Sd>,<Se>,<Sf>,...  ← line 2~
```

동일 `(x, y)` 좌표가 연속되면 같은 위치의 여러 프레임으로 처리된다.
`(-1, -1)` 좌표는 `baseline`으로 처리된다.
