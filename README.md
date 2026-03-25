<div align="center">

# 📊 MultiFactor Quant Study

### SNU Quant Project — 멀티팩터 전략 연구

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br>

> **멀티팩터 모델을 직접 설계하고 백테스팅하여, S&P 500 수익률을 초과하는 나만의 전략을 만들어보자!**

---

</div>

## 🎯 프로젝트 개요

| 항목 | 내용 |
|:---:|:---|
| **목표** | 멀티팩터 포트폴리오를 구성하고 백테스팅을 통해 S&P 500 벤치마크 대비 초과 수익률 달성 |
| **기반 자료** | `Ch5.Multifactor.ipynb` — 강의 제공 멀티팩터 전략 코드 |
| **핵심 과제** | 기존 팩터를 수정·개선하여 **더 좋은 성과를 내는 팩터 조합** 찾기 |
| **데이터** | FMP(Financial Modeling Prep) API 기반 미국 주식 데이터 |

---

## 📂 프로젝트 구조

```
MultiFactor/
├── 📓 Ch5.Multifactor.ipynb      # 멀티팩터 전략 (기본 코드)
├── 📓 Ch5_Backtrader.ipynb       # Backtrader 백테스팅
├── 📓 Ch6. 나만의 퀀트 ETF.ipynb  # 퀀트 ETF 구성
├── 📁 DataBase/                   # 백테스트 데이터 (parquet)
├── 📁 report/                     # 분석 리포트
├── 📁 _fund_cache/                # 펀드 캐시 데이터
├── 📄 backtest_universe_3000.json # 백테스트 유니버스
├── 📄 run.ps1                     # 실행 스크립트
└── 📄 README.md                   # 이 파일
```

---

## 🚀 스터디 진행 방식

### 워크플로우

```
1️⃣  레포 클론         →  내 컴퓨터에 코드 가져오기
2️⃣  브랜치 생성        →  내 이름으로 브랜치 만들기
3️⃣  팩터 수정 & 실험   →  노트북에서 팩터 조합 바꿔보기
4️⃣  결과 저장 & 푸시   →  내 결과를 GitHub에 올리기
5️⃣  결과 비교 & 토론   →  서로의 브랜치를 보며 토론
```

> 💡 **PR(Pull Request) 없이, 각자 브랜치에 결과를 올리는 방식**으로 진행합니다.  
> 협업하여 하나의 코드로 통일하는 것이 아니라, **각자의 실험 결과를 공유**하는 것이 목적입니다.

---

## 🛠️ GitHub 사용법 (초보자 가이드)

### Step 1: 레포지토리 클론하기

터미널(PowerShell 또는 Git Bash)을 열고 아래 명령어를 입력합니다:

```bash
git clone https://github.com/SNU-quant-project/MultiFactor.git
cd MultiFactor
```

> ⚠️ **Git이 설치되어 있지 않다면?**  
> 👉 [Git 다운로드](https://git-scm.com/downloads) 에서 설치하세요.

---

### Step 2: 내 이름으로 브랜치 만들기

```bash
# 브랜치 생성 & 이동 (예: 본인 이름 사용)
git checkout -b 홍길동
```

이렇게 하면 `홍길동`이라는 이름의 브랜치가 만들어지고, 자동으로 그 브랜치로 이동합니다.

---

### Step 3: 팩터 수정 & 실험하기

`Ch5.Multifactor.ipynb`를 Jupyter Notebook에서 열고, 팩터를 수정하며 실험합니다.

```bash
jupyter notebook Ch5.Multifactor.ipynb
```

**실험 예시:**
- 기존 팩터의 가중치 변경
- 새로운 팩터 추가 (모멘텀, 변동성 등)
- 팩터 스크리닝 기준 변경
- 리밸런싱 주기 조정

---

### Step 4: 수정한 파일을 GitHub에 올리기

실험이 끝났으면, 결과를 GitHub에 올립니다:

```bash
# 1. 변경된 파일 확인
git status

# 2. 변경된 파일 전체 추가
git add .

# 3. 커밋 메시지 작성 (무엇을 바꿨는지 간단히)
git commit -m "모멘텀 팩터 추가, 가중치 조정 실험"

# 4. GitHub에 내 브랜치 올리기
git push origin 홍길동
```

> 📌 **커밋 메시지 팁**: 어떤 팩터를 바꿨는지, 결과가 어땠는지 간단히 적어주세요!  
> 예: `"PER 팩터 제거, ROE+모멘텀 조합 → 연 12% 초과수익"`

---

### Step 5: 다른 사람의 결과 보기

```bash
# 다른 사람의 브랜치 가져오기
git fetch origin

# 다른 사람의 브랜치로 이동해서 결과 확인
git checkout origin/김철수
```

또는 **GitHub 웹사이트**에서 브랜치를 전환하여 확인할 수도 있습니다:

> GitHub 레포 페이지 → 좌측 상단 `main ▼` 드롭다운 → 원하는 브랜치 선택

---

## 📋 자주 쓰는 Git 명령어 요약

| 명령어 | 설명 |
|:---|:---|
| `git clone <URL>` | 레포를 내 컴퓨터에 복사 |
| `git checkout -b <이름>` | 새 브랜치 만들고 이동 |
| `git status` | 변경된 파일 확인 |
| `git add .` | 모든 변경 파일 스테이징 |
| `git commit -m "메시지"` | 변경사항 저장 (커밋) |
| `git push origin <브랜치>` | GitHub에 업로드 |
| `git pull origin main` | 최신 코드 가져오기 |
| `git fetch origin` | 원격 브랜치 정보 업데이트 |
| `git checkout origin/<브랜치>` | 다른 사람 브랜치 확인 |

---

## ⚠️ 주의사항

> [!IMPORTANT]
> **대용량 데이터 파일** (`DataBase/` 폴더의 parquet 파일 등)은 **git에 올리지 마세요!**  
> `.gitignore`에 추가하여 제외하는 것을 권장합니다.

```bash
# .gitignore에 추가할 내용
DataBase/
_fund_cache/
.ipynb_checkpoints/
.venv/
__pycache__/
```

---

## 👥 팀 멤버

| 이름 | 브랜치 | 실험 내용 |
|:---:|:---:|:---|
| (이름) | `브랜치명` | 실험 설명 |
| (이름) | `브랜치명` | 실험 설명 |
| (이름) | `브랜치명` | 실험 설명 |

> 📝 각자 실험 후 위 표를 업데이트해주세요!

---

<div align="center">

### 🔬 좋은 팩터를 찾아 S&P 500을 이겨봅시다! 💪

**SNU Quant Project © 2026**

</div>
