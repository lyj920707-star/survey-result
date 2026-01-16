"""
리커트 척도 응답을 숫자로 변환하는 스크립트

변환 규칙:
- 매우 그렇다 → 5
- 그렇다 → 4
- 보통이다 → 3
- 그렇지 않다 → 2
- 매우 그렇지 않다 → 1
"""

import chardet
import pandas as pd
from pathlib import Path


# 리커트 척도 변환 매핑
LIKERT_MAP = {
    '매우 그렇다': 5,
    '그렇다': 4,
    '보통이다': 3,
    '그렇지 않다': 2,
    '매우 그렇지 않다': 1,
}

# 리커트 척도 값 집합 (컬럼 식별용)
LIKERT_VALUES = set(LIKERT_MAP.keys())


def detect_encoding(file_path: Path) -> str:
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def is_likert_column(series: pd.Series) -> bool:
    """해당 컬럼이 리커트 척도 컬럼인지 확인합니다."""
    # 빈 값이 아닌 값들만 확인
    non_empty_values = series.dropna().astype(str).str.strip()
    non_empty_values = non_empty_values[non_empty_values != '']

    if len(non_empty_values) == 0:
        return False

    # 모든 비어있지 않은 값이 리커트 척도 값인지 확인
    unique_values = set(non_empty_values.unique())
    return unique_values.issubset(LIKERT_VALUES)


def convert_likert_value(value) -> str:
    """리커트 척도 텍스트를 숫자로 변환합니다."""
    if pd.isna(value):
        return value

    str_value = str(value).strip()
    if str_value in LIKERT_MAP:
        return LIKERT_MAP[str_value]
    return value


def process_file(input_path: Path, output_path: Path) -> bool:
    """CSV 파일의 리커트 척도를 숫자로 변환합니다."""
    try:
        # 인코딩 감지 및 파일 읽기
        encoding = detect_encoding(input_path)
        print(f"  감지된 인코딩: {encoding}")

        df = pd.read_csv(input_path, encoding=encoding)
        print(f"  총 {len(df)}개 응답, {len(df.columns)}개 컬럼")

        # 리커트 척도 컬럼 식별 및 변환
        likert_columns = []
        for col in df.columns:
            if is_likert_column(df[col]):
                likert_columns.append(col)
                df[col] = df[col].apply(convert_likert_value)

        print(f"  변환된 리커트 척도 컬럼: {len(likert_columns)}개")

        # 출력 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # UTF-8로 저장 (pandas 기본 처리)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        return True

    except Exception as e:
        print(f"  오류 발생: {e}")
        return False


def process_all_files(work_folder: str):
    """작업 폴더의 raw 폴더에 있는 모든 CSV 파일을 변환합니다.

    Args:
        work_folder: 작업 폴더명 (예: '2024_상반기_신입사원_입문과정')
    """
    base_dir = Path(__file__).parent.parent.parent
    work_dir = base_dir / 'data' / work_folder

    if not work_dir.exists():
        print(f"작업 폴더가 존재하지 않습니다: {work_folder}")
        return

    raw_dir = work_dir / 'raw'
    output_dir = work_dir / 'processed'

    csv_files = list(raw_dir.glob('*.csv'))

    if not csv_files:
        print(f"[{work_folder}] 변환할 CSV 파일이 없습니다.")
        return

    print(f"[{work_folder}] {len(csv_files)}개의 파일을 변환합니다.\n")

    success_count = 0
    for csv_file in csv_files:
        output_file = output_dir / csv_file.name
        print(f"변환 중: {csv_file.name}")

        if process_file(csv_file, output_file):
            print(f"  완료: {output_file.name}\n")
            success_count += 1
        else:
            print(f"  실패: {csv_file.name}\n")

    print(f"변환 완료: {success_count}/{len(csv_files)} 파일")


if __name__ == '__main__':
    process_all_files()
