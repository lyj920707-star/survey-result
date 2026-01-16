# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

교육 만족도 설문조사 결과를 처리하는 유틸리티 프로젝트입니다.
- 리커트 척도 응답을 숫자로 변환 (매우 그렇다=5 ~ 매우 그렇지 않다=1)
- 문항별 평균 계산
- 템플릿에 결과 자동 입력 (유사도 기반 문항 매핑)
- 매핑 검토 리포트 생성

## 명령어

```bash
# 의존성 설치
pip install -r requirements.txt

# 전체 파이프라인 실행 (작업 폴더 지정 필수)
python scripts/run_all.py 2024_상반기_신입사원_입문과정

# 개별 단계 실행
python scripts/run_preprocessing.py 2024_상반기_신입사원_입문과정   # 전처리만
python scripts/run_analysis.py 2024_상반기_신입사원_입문과정        # 분석만
python scripts/run_reporting.py 2024_상반기_신입사원_입문과정       # 리포팅만
```

## 아키텍처

```
survey-result/
├── data/
│   └── {과정폴더}/           # 예: 2024_상반기_신입사원_입문과정
│       ├── raw/              # 원본 CSV 파일 (설문 응답)
│       ├── processed/        # 리커트 척도 → 숫자 변환된 CSV
│       ├── results/          # 문항별 평균 등 분석 결과 (JSON)
│       └── output/           # 최종 산출물 (템플릿에 결과 반영)
│
├── templates/                # 결과 입력용 템플릿 파일 (.xlsx)
│
├── scripts/                  # 실행 스크립트
│   ├── run_all.py            # 전체 파이프라인 실행
│   ├── run_preprocessing.py  # 전처리 실행
│   ├── run_analysis.py       # 분석 실행
│   └── run_reporting.py      # 리포팅 실행
│
├── src/                      # 모듈 코드
│   ├── preprocessing/        # 데이터 전처리
│   │   ├── convert_encoding.py   # 인코딩 변환 (ANSI/CP949 → UTF-8)
│   │   └── convert_likert.py     # 리커트 척도 → 숫자 변환
│   ├── analysis/             # 데이터 분석
│   │   └── calculate_stats.py    # 문항별 평균, 최소, 최대 계산
│   └── reporting/            # 결과 출력
│       └── fill_template.py      # 유사도 기반 문항 매핑 및 템플릿 작성
│
├── requirements.txt
└── CLAUDE.md
```

## 워크플로우

```
[1단계] 전처리 (preprocessing)
    data/{과정}/raw/*.csv → convert_likert.py → data/{과정}/processed/*.csv

[2단계] 분석 (analysis)
    data/{과정}/processed/*.csv → calculate_stats.py → data/{과정}/results/*_stats.json

[3단계] 리포팅 (reporting)
    data/{과정}/results/*_stats.json + templates/*.xlsx
        → fill_template.py
        → data/{과정}/output/*_결과.xlsx
        → data/{과정}/output/*_검토리포트.json
```

## 리커트 척도 변환 규칙

| 응답 | 점수 |
|------|------|
| 매우 그렇다 | 5 |
| 그렇다 | 4 |
| 보통이다 | 3 |
| 그렇지 않다 | 2 |
| 매우 그렇지 않다 | 1 |

## 템플릿 자동 매핑

리포팅 단계에서 설문 문항과 템플릿 문항을 유사도 기반으로 자동 매핑합니다.
- 템플릿 H열의 문항과 설문 문항을 비교
- 유사도 50% 이상일 때 매핑 성공
- J열에 해당 문항의 평균값 입력
- 매핑 결과는 `_검토리포트.json`으로 저장 (수동 검토용)
