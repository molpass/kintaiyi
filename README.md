<div align="center">

# 🌟 Python 太乙神數(태을신수) | Kintaiyi 堅太乙

### 예부터 군왕과 관신이 귀히 여겨, 위로 천문을 아래로 국운을 점치는 데 반드시 쓰였던 법 — 가장 풍부한 오픈소스 태을신수 포국 도구

*The most authentic open-source Taiyi Shenshu (太乙神數) divination engine in Python*

[![PyPI version](https://img.shields.io/pypi/v/kintaiyi?color=blue&label=PyPI)](https://pypi.org/project/kintaiyi/)
[![Python](https://img.shields.io/pypi/pyversions/kintaiyi?label=Python)](https://pypi.org/project/kintaiyi/)
[![Downloads](https://img.shields.io/pypi/dm/kintaiyi?color=green&label=Downloads)](https://pypi.org/project/kintaiyi/)
[![CI](https://github.com/kentang2017/kintaiyi/actions/workflows/ci.yml/badge.svg)](https://github.com/kentang2017/kintaiyi/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/kentang2017/kintaiyi?style=social)](https://github.com/kentang2017/kintaiyi)

<br/>

[🚀 **지금 온라인 체험 Live Demo**](https://kintaiyi.streamlitapp.com) &nbsp;|&nbsp; [🎬 **YouTube 소개**](https://www.youtube.com/watch?v=FKnPu8FOIlc) &nbsp;|&nbsp; [📦 **PyPI**](https://pypi.org/project/kintaiyi/) &nbsp;|&nbsp; [📖 **Wiki**](https://github.com/kentang2017/kintaiyi/wiki)

<br/>

![太乙神數盤圖](https://github.com/kentang2017/kintaiyi/blob/master/pic/Untitled-1.png?raw=true)


</div>

> 🇰🇷 이 저장소는 **molpass가 포크한 사본**입니다. 원문(中文·English)은 [README.en.md](./README.en.md)를 참고하세요.

---

## 📑 목차 Table of Contents

- [✨ 하이라이트 Highlights](#-하이라이트-highlights)
- [📖 소개 Introduction](#-소개-introduction)
- [🚀 빠른 시작 Quick Start](#-빠른-시작-quick-start)
- [📋 지원 기능 Features](#-지원-기능-features)
- [🖼️ 스크린샷과 데모 Screenshots & Demo](#️-스크린샷과-데모-screenshots--demo)
- [📦 설치 Installation](#-설치-installation)
- [🔧 고급 사용법 Advanced Usage](#-고급-사용법-advanced-usage)
- [🤝 기여 안내 Contributing](#-기여-안내-contributing)
- [📄 License](#-license)

---

## ✨ 하이라이트 Highlights

- 🔮 **여섯 가지 계법 완비** — 연계(年計)·월계(月計)·일계(日計)·시계(時計)·분계(分計)·명법(命法), 모든 태을 추산 상황을 망라
  **Six Calculation Modes** — Year, Month, Day, Hour, Minute, and Life Destiny, covering all Taiyi divination scenarios
- 📜 **4대 고법 병존** — 태을통종(太乙統宗)·태을금경(太乙金鏡)·태을도금가(太乙淘金歌)·태을국(太乙局), 정통 고법을 단순화하지 않음
  **Four Classical Methods** — Taiyi Tongzong, Taiyi Jinjing, Taiyi Taojin Ge, and Taiyi Ju — authentic ancient formulas without simplification
- 📊 **풍부한 출력 내용** — 간지·국식·신살·이십팔수·팔문·팔궁 왕쇠·병진 예측·역사 연호 대응
  **Rich Output** — Stems & Branches, board configuration, spirit indicators, 28 Lunar Mansions, Eight Gates, palace prosperity, battle predictions, and historical reign-year mapping
- 🏯 **역사 연호 대조** — 중국 역대 기년과 음력 환산을 완비 내장
  **Historical Reign-Year Mapping** — Built-in complete Chinese dynastic chronology and lunar calendar conversion
- 🖥️ **다양한 사용 방식** — Python API + Typer CLI + Streamlit 그래픽 인터페이스, 필요에 맞게 선택
  **Multiple Interfaces** — Python API + Typer CLI + Streamlit web GUI — use whichever suits your needs
- 🤖 **AI 지능 분석** — Cerebras AI를 통합하여 반면(盤面)을 자동 해석
  **AI-Powered Analysis** — Integrated with Cerebras AI for automatic board interpretation

---

## 📖 소개 Introduction

**태을신수(太乙神數)**는 기문둔갑·대육임과 더불어 「삼식(三式)」으로 불리며, 중국 고대 최고 수준의 술수 체계 중 하나로 천시(天時)와 국운, 역사 변화의 규율을 추산하는 데 전문적으로 쓰였습니다. 그 법은 《역위·건착도(易緯·乾鑿度)》의 태을 행구궁법(行九宮法)에서 비롯되었으며, 황제(黃帝)가 치우(蚩尤)와 싸우던 때 시작되어 3천여 년간 이어져 왔다고 전합니다.

**Tai Yi Shen Shu (太乙神數)**, together with Qi Men Dun Jia (奇門遁甲) and Da Liu Ren (大六壬), is known as the "Three Styles" (三式) — one of the highest-level divination systems in ancient China, specifically used for predicting celestial timing, national fortune, and historical patterns. The method originates from the *Yi Wei · Qian Zao Du* (易緯·乾鑿度) and the Taiyi Nine Palace traversal, said to date back to the era of the Yellow Emperor's battle against Chi You — over three thousand years ago.

**Kintaiyi 堅太乙**는 「고법을 굳건히 지킨다(堅守古法)」는 뜻입니다. 본 패키지는 고서의 기록을 엄격히 따라 알고리즘을 구현하며, 단순화하거나 생략하지 않습니다. 태을신수 연구자와 애호가에게 **검증 가능하고 재현 가능한** 오픈소스 도구를 제공하는 것이 목표입니다. 연운 추산, 국사 예측, 개인 명리 어느 것이든 한 번에 포국할 수 있습니다.

**Kintaiyi (堅太乙)** means "steadfastly upholding ancient methods." This library strictly follows classical texts to implement its algorithms — no simplification, no omission — aiming to provide researchers and enthusiasts with a **verifiable and reproducible** open-source tool. Whether for yearly fortune prediction, national affairs forecasting, or personal destiny analysis, a complete divination board can be generated with a single command.

---

## 🚀 빠른 시작 Quick Start

### 설치 Installation

```bash
pip install kintaiyi
```

CLI 또는 Web 인터페이스 선택 설치 / Optional extras for CLI or Web interface：

```bash
pip install kintaiyi[cli]       # 命令列工具 / Command-line tool (Typer CLI)
pip install kintaiyi[app]       # Streamlit 圖形介面 / Streamlit GUI
pip install kintaiyi[cli,app]   # 全部安裝 / Install all
```

### Python 코드 예시 Python Code Example

```python
from kintaiyi.kintaiyi import Taiyi

# 排一個年計太乙盤 (Calculate a yearly Taiyi board)
result = Taiyi(2026, 3, 24, 12, 30).pan(ji_style=0, method=1)
print(result["太乙計"])       # → 年計
print(result["局式"])         # → {'文': '陽遁...', '數': ..., ...}
print(result["二十八宿值日"])  # → 二十八宿值日星
print(result["推主客相闗法"])  # → 主客勝負判斷
```

### CLI 명령줄 예시 CLI Examples

```bash
# 年計排盤 / Year calculation board
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode year --method 1

# 日計排盤，輸出 JSON / Day calculation board, output as JSON
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode day --output json

# 命法推算 / Life destiny calculation
kintaiyi calculate --date 1990-05-15 --time 08:00 --mode life --sex male
```

### Streamlit 원클릭 실행 Streamlit Quick Launch

```bash
pip install kintaiyi[app]
streamlit run apps/streamlit_app.py
```

---

## 📋 지원 기능 Features

### 계법 모드 Calculation Modes

| 모드 Mode | ji_style | 설명 Description |
|-----------|----------|-----------------|
| 연계 Year | `0` | 연운·국운 대세 추산 / Predict yearly and national fortune trends |
| 월계 Month | `1` | 월별 기운 길흉 추산 / Predict monthly auspiciousness and energy flow |
| 일계 Day | `2` | 일과(日課) 길흉 추산 / Predict daily auspiciousness |
| 시계 Hour | `3` | 시진 길흉 추산 / Predict hourly auspiciousness |
| 분계 Minute | `4` | 현대적 확장, 분 단위 정밀 / Modern extension, precise to the minute |
| 명법 Life | `5` | 개인 명리 추산 / Personal destiny calculation |

### 고법 공식 Taiyi Methods

| 방법 Method | method | 출처 Source |
|------------|--------|------------|
| 태을통종 Taiyi Tongzong | `0` | 《太乙統宗寶鑑》*Taiyi Tongzong Baojian* |
| 태을금경 Taiyi Jinjing | `1` | 《太乙金鏡式經》*Taiyi Jinjing Shi Jing* |
| 태을도금가 Taiyi Taojin Ge | `2` | 《太乙淘金歌》*Taiyi Taojin Ge* |
| 태을국 Taiyi Ju | `3` | 《太乙局》*Taiyi Ju* |

### 출력 내용 Output Fields

반면 출력은 다음 정보를 포함합니다(Output includes but is not limited to)：

- **기본 정보** — 서기 날짜·음력·간지 오주(五柱)·역사 연호 / Basic Info — Gregorian date, lunar date, Five Pillars (stems & branches), historical reign year
- **국식** — 음양둔·국수·적년수·기원 / Board Configuration — Yin/Yang escape, board number, accumulated years, epoch
- **태을 제신(諸神)** — 태을·천을·지을·사신·직부·문창·계신·합신 / Taiyi Spirits — Taiyi, Tianyi, Diyi, Four Spirits, Zhifu, Wenchang, Jishen, Heshen
- **주객산(主客算)** — 주산·객산·정산, 삼재수(三才數)와 격국 판단 포함 / Host & Guest Calculations — host count, guest count, fixed count, including Three Powers (San Cai) numbers and pattern analysis
- **팔문 팔궁** — 팔문 치사(値事)와 분포, 팔궁 왕쇠 / Eight Gates & Eight Palaces — gate assignments, distribution, and palace prosperity
- **이십팔수** — 치일수(値日宿)·태세수·시격수(始擊宿) 및 단사(斷事) / 28 Lunar Mansions — duty mansion, Tai Sui mansion, initial-strike mansion, and interpretations
- **병진 예측** — 추주객상관법·비조조전법·풍운 제법 / Battle Predictions — host-guest analysis, flying-bird battle assistance, wind-cloud techniques
- **7대 병법** — 뇌공입수·임진문도·사자반척·백운권공·맹호상거·백룡득운·회군무언 / Seven Military Strategies — Thunder Lord Enters Water, Asking the Way at the Ford, Lion's Reverse Throw, White Cloud Rolls the Sky, Fierce Tiger Standoff, White Dragon Seizes Cloud, Silent Army Retreat

---

## 🖼️ 스크린샷과 데모 Screenshots & Demo

### 온라인 데모 Live Demo

👉 [**https://kintaiyi.streamlitapp.com**](https://kintaiyi.streamlitapp.com)

> 📌 중국 본토 사용자는 VPN이 필요할 수 있습니다 *(Mainland China users may need a VPN)*

### 반도(盤圖) 미리보기 Board Preview

<div align="center">

![太乙九宮分野圖](https://github.com/kentang2017/kintaiyi/blob/master/pic/%E5%A4%AA%E4%B9%99%E4%B9%9D%E5%AE%AE%E5%88%86%E9%87%8E%E5%9C%96.jpg?raw=true)

*태을 구궁 분야도 — Taiyi Nine Palace Sector Diagram*

</div>

---

## 📦 설치 Installation

### 환경 요구사항 Requirements

- Python ≥ 3.10

### 기본 설치 Basic Installation

```bash
pip install kintaiyi
```

### 선택 의존성 Optional Extras

```bash
# CLI 命令列工具（基於 Typer）/ CLI command-line tool (based on Typer)
pip install kintaiyi[cli]

# Streamlit 圖形介面（完整 Web 應用）/ Streamlit GUI (full web application)
pip install kintaiyi[app]

# Flask Web 後端 / Flask web backend
pip install kintaiyi[web]

# 開發環境（pytest + ruff）/ Development environment (pytest + ruff)
pip install kintaiyi[dev]
```

### 소스에서 설치 Install from Source

```bash
git clone https://github.com/kentang2017/kintaiyi.git
cd kintaiyi
pip install -e ".[cli,app,dev]"
```

---

## 🔧 고급 사용법 Advanced Usage

### CLI 전체 옵션 CLI Options

```
kintaiyi calculate [OPTIONS]
```

| 옵션 Option | 약어 | 설명 Description | 기본값 Default |
|-------------|------|-----------------|---------------|
| `--year` | `-y` | 서기 연도 Year | 현재 연도 Current |
| `--month` | `-m` | 월 Month | 현재 월 Current |
| `--day` | `-d` | 일 Day | 현재 날짜 Current |
| `--hour` | `-H` | 시 Hour (0-23) | 현재 시 Current |
| `--minute` | `-M` | 분 Minute (0-59) | 현재 분 Current |
| `--date` | | 날짜 Date (YYYY-MM-DD) | — |
| `--time` | | 시간 Time (HH:MM) | — |
| `--mode` | | 계법 모드 Calculation mode | `year` |
| `--method` | | 고법 공식 Classical method (0-3) | `0` |
| `--output` | `-o` | 출력 형식 Output format (text/json/markdown) | `text` |
| `--sex` | `-s` | 성별(명법 시 필수: male/female) Sex (required for life mode) | — |

```bash
# 查看版本 / Check version
kintaiyi version

# 使用個別參數 / Using individual parameters
kintaiyi calculate --year 1552 --month 9 --day 24 --hour 0 --minute 0 --mode year --method 1

# 使用日期字串 + JSON 輸出 / Using date string + JSON output
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode day --output json

# Markdown 表格輸出 / Markdown table output
kintaiyi calculate --date 2026-03-24 --time 12:30 --mode hour --output markdown
```

### Python API

```python
from kintaiyi.kintaiyi import Taiyi

# 建立太乙物件 / Create a Taiyi object
taiyi = Taiyi(year=2026, month=3, day=24, hour=12, minute=30)

# 排盤 / Generate board
# ji_style: 0=年計 Year, 1=月計 Month, 2=日計 Day, 3=時計 Hour, 4=分計 Minute
# method:   0=統宗 Tongzong, 1=金鏡 Jinjing, 2=淘金歌 Taojin Ge, 3=太乙局 Taiyi Ju
result = taiyi.pan(ji_style=0, method=1)

# 命法推算 / Life destiny calculation
# Python API 使用中文 "男"/"女"；CLI 使用 male/female (Python API uses Chinese "男"/"女"; CLI uses male/female)
life_result = taiyi.taiyi_life(sex="男")  # "男" or "女"

# 結果為 dict，可直接轉 JSON / Result is a dict, can be directly converted to JSON
import json
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 출력 예시 Sample Output

```python
from kintaiyi.kintaiyi import Taiyi

result = Taiyi(1552, 9, 24, 0, 0).pan(ji_style=0, method=1)

# result 為 dict，包含 / result is a dict containing:
# {
#   "太乙計": "年計",                    # Calculation mode: Year
#   "太乙公式類別": "太乙金鏡",            # Method: Taiyi Jinjing
#   "公元日期": "1552年9月24日0時",        # Gregorian date
#   "干支": ["壬子", "庚戌", "丙戌", "戊子", "甲子"],  # Stems & Branches
#   "農曆": {"年": 1552, "月": 9, "日": 7},            # Lunar calendar
#   "年號": "明世宗朱厚熜 嘉靖三十一年",    # Historical reign year
#   "局式": {"文": "陽遁十三局", "數": 13, ...},  # Board config
#   "太乙落宮": 6,                        # Taiyi palace position
#   "太乙": "兌",                          # Taiyi trigram
#   "二十八宿值日": "翼",                  # 28 Mansions duty star
#   "推主客相闗法": "主尅客，主勝",         # Host-guest analysis
#   ...
# }
```

---

## 🤝 기여 안내 Contributing

모든 형태의 기여를 환영합니다! *All contributions are welcome!*

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md) 참고 / See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

- 🐛 **버그 제보** — [Issue](https://github.com/kentang2017/kintaiyi/issues) 제출 / Report bugs via Issues
- ✨ **새 기능** — 새 고법·새 계법 추가 PR 환영 / PRs welcome for new methods and features
- 📚 **과례 검증** — 역사 과례를 제공해 알고리즘 정확성 검증 / Provide historical examples to verify algorithm accuracy
- 🌐 **번역** — 문서나 용어 번역 협력 / Help translate documentation or terminology
- ⭐ **Star** — 가장 간단한 후원 방법! / The easiest way to show your support!

### 개발 환경 설정 Development Setup

```bash
git clone https://github.com/kentang2017/kintaiyi.git
cd kintaiyi
pip install -e ".[dev]"

# 運行測試 / Run tests
pytest

# 代碼格式化 / Code formatting
ruff check src/ --fix
ruff format src/
```

---

## 🐛 이슈 Issues

[GitHub Issues](https://github.com/kentang2017/kintaiyi/issues)

---

## 📄 License

[MIT License](LICENSE)
