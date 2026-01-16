# 교육 만족도 설문 결과 처리 시스템

교육 프로그램 만족도 설문조사 결과를 자동으로 처리하여 리포트 템플릿에 입력하는 유틸리티입니다.

## 주요 기능

- **리커트 척도 변환**: 텍스트 응답(매우 그렇다 ~ 매우 그렇지 않다)을 숫자(5~1)로 변환
- **통계 분석**: 문항별 평균, 최소, 최대값 계산
- **자동 매핑**: 설문 문항과 템플릿 문항을 유사도 기반으로 자동 매칭
- **검토 리포트**: 매핑 결과를 JSON으로 저장하여 수동 검토 지원

## 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 1. 데이터 준비

```
data/{과정폴더}/raw/   에 원본 CSV 파일 배치
```

예: `data/2024_상반기_신입사원_입문과정/raw/설문결과.csv`

### 2. 파이프라인 실행

```bash
# 전체 파이프라인 실행
python scripts/run_all.py 2024_상반기_신입사원_입문과정

# 개별 단계 실행
python scripts/run_preprocessing.py 2024_상반기_신입사원_입문과정   # 전처리
python scripts/run_analysis.py 2024_상반기_신입사원_입문과정        # 분석
python scripts/run_reporting.py 2024_상반기_신입사원_입문과정       # 리포팅
```

### 3. 결과 확인

```
data/{과정폴더}/output/   에서 결과 파일 확인
├── *_결과.xlsx           # 템플릿에 평균값이 입력된 파일
└── *_검토리포트.json     # 매핑 결과 (검토용)
```

## 프로젝트 구조

```
survey-result/
├── data/
│   └── {과정폴더}/
│       ├── raw/              # 원본 CSV
│       ├── processed/        # 숫자 변환된 CSV
│       ├── results/          # 분석 결과 JSON
│       └── output/           # 최종 산출물
│
├── templates/                # 결과 입력용 템플릿 (.xlsx)
├── scripts/                  # 실행 스크립트
├── src/                      # 모듈 코드
│   ├── preprocessing/        # 데이터 전처리
│   ├── analysis/             # 통계 분석
│   └── reporting/            # 템플릿 작성
│
└── requirements.txt
```

## 처리 흐름

```
[1] 전처리
    raw/*.csv → 리커트 변환 → processed/*.csv

[2] 분석
    processed/*.csv → 통계 계산 → results/*_stats.json

[3] 리포팅
    results/*.json + templates/*.xlsx → output/*_결과.xlsx
                                      → output/*_검토리포트.json
```

## 리커트 척도 변환 규칙

| 응답 | 점수 |
|------|------|
| 매우 그렇다 | 5 |
| 그렇다 | 4 |
| 보통이다 | 3 |
| 그렇지 않다 | 2 |
| 매우 그렇지 않다 | 1 |

## 템플릿 매핑

리포팅 단계에서 설문 문항과 템플릿 문항을 자동으로 매칭합니다.

- 유사도 50% 이상일 때 매핑 성공
- 템플릿 H열(문항) → J열(평균값) 입력
- 매핑 실패 항목은 검토리포트에서 확인 가능
