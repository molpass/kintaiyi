# Python 太乙神數(태을신수) | Kintaiyi 堅太乙

예부터 군왕과 관신이 귀히 여겨, 위로 천문을 아래로 국운을 점치는 데 반드시 쓰였던 법 — 풍부한 오픈소스 태을신수 포국 도구.

> 이 저장소는 molpass가 포크한 사본입니다. 원문(중국어·영어)은 [README.en.md](./README.en.md)를 참고하세요.

링크: [온라인 체험](https://kintaiyi.streamlitapp.com) · [YouTube 소개](https://www.youtube.com/watch?v=FKnPu8FOIlc) · [PyPI](https://pypi.org/project/kintaiyi/) · [Wiki](https://github.com/kentang2017/kintaiyi/wiki)

---

## 하이라이트

- **여섯 가지 계법 완비** — 연계(年計)·월계(月計)·일계(日計)·시계(時計)·분계(分計)·명법(命法), 모든 태을 추산 상황을 망라
- **4대 고법 병존** — 태을통종(太乙統宗)·태을금경(太乙金鏡)·태을도금가(太乙淘金歌)·태을국(太乙局), 정통 고법을 단순화하지 않음
- **풍부한 출력 내용** — 간지·국식·신살·이십팔수·팔문·팔궁 왕쇠·병진 예측·역사 연호 대응
- **역사 연호 대조** — 중국 역대 기년과 음력 환산을 완비 내장
- **다양한 사용 방식** — Python API + Typer CLI + Streamlit 그래픽 인터페이스, 필요에 맞게 선택
- **AI 지능 분석** — Cerebras AI를 통합하여 반면(盤面)을 자동 해석

---

## 소개

**태을신수(太乙神數)**는 기문둔갑·대육임과 더불어 「삼식(三式)」으로 불리며, 중국 고대 최고 수준의 술수 체계 중 하나로 천시(天時)와 국운, 역사 변화의 규율을 추산하는 데 전문적으로 쓰였습니다. 그 법은 《역위·건착도(易緯·乾鑿度)》의 태을 행구궁법(行九宮法)에서 비롯되었으며, 황제(黃帝)가 치우(蚩尤)와 싸우던 때 시작되어 3천여 년간 이어져 왔다고 전합니다.

**Kintaiyi 堅太乙**는 「고법을 굳건히 지킨다(堅守古法)」는 뜻입니다. 본 패키지는 고서의 기록을 엄격히 따라 알고리즘을 구현하며, 단순화하거나 생략하지 않습니다. 태을신수 연구자와 애호가에게 **검증 가능하고 재현 가능한** 오픈소스 도구를 제공하는 것이 목표입니다. 연운 추산, 국사 예측, 개인 명리 어느 것이든 한 번에 포국할 수 있습니다.

---

## 빠른 시작

### 설치

```bash
pip install kintaiyi
```

CLI 또는 Web 인터페이스 선택 설치:

```bash
pip install kintaiyi[cli]       # 명령줄 도구 (Typer CLI)
pip install kintaiyi[app]       # Streamlit 그래픽 인터페이스
pip install kintaiyi[cli,app]   # 전부 설치
```

### Python 코드 예시

```python
from kintaiyi.kintaiyi import Taiyi

# 연계 태을 포국 계산
result = Taiyi(2026, 3, 24, 12, 30).pan(ji_style=0, method=1)
print(result["太乙計"])       # → 年計 (계법)
print(result["局式"])         # → {'文': '陽遁...', '數': ..., ...}
print(result["二十八宿值日"])  # → 이십팔수 치일성
print(result["推主客相闗法"])  # → 주객 승부 판단
```

### CLI 명령줄 예시

```bash
# 연계 포국
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode year --method 1

# 일계 포국, JSON 출력
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode day --output json

# 명법 추산
kintaiyi calculate --date 1990-05-15 --time 08:00 --mode life --sex male
```

### Streamlit 원클릭 실행

```bash
pip install kintaiyi[app]
streamlit run apps/streamlit_app.py
```

---

## 지원 기능

### 계법 모드

| 모드 | ji_style | 설명 |
|-----------|----------|-----------------|
| 연계(年計) | `0` | 연운·국운 대세 추산 |
| 월계(月計) | `1` | 월별 기운 길흉 추산 |
| 일계(日計) | `2` | 일과(日課) 길흉 추산 |
| 시계(時計) | `3` | 시진 길흉 추산 |
| 분계(分計) | `4` | 현대적 확장, 분 단위 정밀 |
| 명법(命法) | `5` | 개인 명리 추산 |

### 고법 공식

| 방법 | method | 출처 |
|------------|--------|------------|
| 태을통종(太乙統宗) | `0` | 《太乙統宗寶鑑》 |
| 태을금경(太乙金鏡) | `1` | 《太乙金鏡式經》 |
| 태을도금가(太乙淘金歌) | `2` | 《太乙淘金歌》 |
| 태을국(太乙局) | `3` | 《太乙局》 |

### 출력 내용

반면 출력은 다음 정보를 포함합니다(이에 한정되지 않음):

- **기본 정보** — 서기 날짜·음력·간지 오주(五柱)·역사 연호
- **국식** — 음양둔·국수·적년수·기원
- **태을 제신(諸神)** — 태을·천을·지을·사신·직부·문창·계신·합신
- **주객산(主客算)** — 주산·객산·정산, 삼재수(三才數)와 격국 판단 포함
- **팔문 팔궁** — 팔문 치사(値事)와 분포, 팔궁 왕쇠
- **이십팔수** — 치일수(値日宿)·태세수·시격수(始擊宿) 및 단사(斷事)
- **병진 예측** — 추주객상관법·비조조전법·풍운 제법
- **7대 병법** — 뇌공입수·임진문도·사자반척·백운권공·맹호상거·백룡득운·회군무언

---

## 설치

### 환경 요구사항

- Python 3.10 이상

### 기본 설치

```bash
pip install kintaiyi
```

### 선택 의존성

```bash
# CLI 명령줄 도구 (Typer 기반)
pip install kintaiyi[cli]

# Streamlit 그래픽 인터페이스 (완전한 Web 앱)
pip install kintaiyi[app]

# Flask Web 백엔드
pip install kintaiyi[web]

# 개발 환경 (pytest + ruff)
pip install kintaiyi[dev]
```

### 소스에서 설치

```bash
git clone https://github.com/kentang2017/kintaiyi.git
cd kintaiyi
pip install -e ".[cli,app,dev]"
```

---

## 고급 사용법

### CLI 전체 옵션

```
kintaiyi calculate [OPTIONS]
```

| 옵션 | 약어 | 설명 | 기본값 |
|-------------|------|-----------------|---------------|
| `--year` | `-y` | 서기 연도 | 현재 연도 |
| `--month` | `-m` | 월 | 현재 월 |
| `--day` | `-d` | 일 | 현재 날짜 |
| `--hour` | `-H` | 시 (0-23) | 현재 시 |
| `--minute` | `-M` | 분 (0-59) | 현재 분 |
| `--date` | | 날짜 (YYYY-MM-DD) | — |
| `--time` | | 시간 (HH:MM) | — |
| `--mode` | | 계법 모드 | `year` |
| `--method` | | 고법 공식 (0-3) | `0` |
| `--output` | `-o` | 출력 형식 (text/json/markdown) | `text` |
| `--sex` | `-s` | 성별(명법 시 필수: male/female) | — |

```bash
# 버전 확인
kintaiyi version

# 개별 파라미터 사용
kintaiyi calculate --year 1552 --month 9 --day 24 --hour 0 --minute 0 --mode year --method 1

# 날짜 문자열 + JSON 출력
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode day --output json

# Markdown 표 출력
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode hour --output markdown
```

### Python API

```python
from kintaiyi.kintaiyi import Taiyi

# 태을 객체 생성
taiyi = Taiyi(year=2026, month=3, day=24, hour=12, minute=30)

# 포국 생성
# ji_style: 0=연계, 1=월계, 2=일계, 3=시계, 4=분계
# method:   0=통종, 1=금경, 2=도금가, 3=태을국
result = taiyi.pan(ji_style=0, method=1)

# 명법 추산
# Python API는 한자 "男"/"女"를 사용, CLI는 male/female를 사용
life_result = taiyi.taiyi_life(sex="男")  # "男" 또는 "女"

# 결과는 dict이며 그대로 JSON으로 변환 가능
import json
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 출력 예시

```python
from kintaiyi.kintaiyi import Taiyi

result = Taiyi(1552, 9, 24, 0, 0).pan(ji_style=0, method=1)

# result는 dict이며 다음을 포함:
# {
#   "太乙計": "年計",                    # 계법 모드: 연계
#   "太乙公式類別": "太乙金鏡",            # 방법: 태을금경
#   "公元日期": "1552年9月24日0時",        # 서기 날짜
#   "干支": ["壬子", "庚戌", "丙戌", "戊子", "甲子"],  # 간지
#   "農曆": {"年": 1552, "月": 9, "日": 7},            # 음력
#   "年號": "明世宗朱厚熜 嘉靖三十一年",    # 역사 연호
#   "局式": {"文": "陽遁十三局", "數": 13, ...},  # 국식
#   "太乙落宮": 6,                        # 태을 낙궁
#   "太乙": "兌",                          # 태을 괘
#   "二十八宿值日": "翼",                  # 이십팔수 치일성
#   "推主客相闗法": "主尅客，主勝",         # 주객 분석
#   ...
# }
```

---

## 이슈

[GitHub Issues](https://github.com/kentang2017/kintaiyi/issues)

---

## 라이선스

[MIT License](LICENSE)
