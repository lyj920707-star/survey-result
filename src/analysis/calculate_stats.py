"""
설문 결과 통계 계산 스크립트

- 각 문항별 평균 계산
- 결과를 JSON 파일로 저장
"""

import json
import pandas as pd
from pathlib import Path


def is_numeric_column(series: pd.Series) -> bool:
    """해당 컬럼이 숫자형(리커트 척도 변환) 컬럼인지 확인합니다."""
    non_empty = series.dropna()
    if len(non_empty) == 0:
        return False

    try:
        numeric_values = pd.to_numeric(non_empty, errors='coerce')
        # 80% 이상이 숫자이고, 값이 1~5 범위인 경우
        valid_count = numeric_values.dropna()
        if len(valid_count) / len(non_empty) < 0.8:
            return False
        return valid_count.between(1, 5).all()
    except:
        return False


def calculate_stats_for_file(input_path: Path) -> dict:
    """CSV 파일의 각 문항별 통계를 계산합니다."""
    df = pd.read_csv(input_path, encoding='utf-8-sig')

    results = {
        'file_name': input_path.name,
        'total_responses': len(df),
        'questions': []
    }

    for col in df.columns:
        if is_numeric_column(df[col]):
            numeric_values = pd.to_numeric(df[col], errors='coerce').dropna()

            question_stats = {
                'question': col,
                'mean': round(numeric_values.mean(), 2),
                'count': int(len(numeric_values)),
                'min': int(numeric_values.min()),
                'max': int(numeric_values.max()),
            }
            results['questions'].append(question_stats)

    return results


def process_file(input_path: Path, output_path: Path) -> bool:
    """단일 파일을 처리하여 통계 결과를 저장합니다."""
    try:
        print(f"  분석 중: {input_path.name}")

        results = calculate_stats_for_file(input_path)

        print(f"  총 응답: {results['total_responses']}개")
        print(f"  분석된 문항: {len(results['questions'])}개")

        # 결과 출력
        print("\n  [문항별 평균]")
        for q in results['questions']:
            # 문항명 축약 (50자)
            q_short = q['question'][:50] + "..." if len(q['question']) > 50 else q['question']
            print(f"    {q['mean']:.2f} | {q_short}")

        # JSON 파일로 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"  오류 발생: {e}")
        return False


def process_all_files(work_folder: str):
    """작업 폴더의 processed 폴더에 있는 모든 CSV 파일을 분석합니다.

    Args:
        work_folder: 작업 폴더명 (예: '2024_상반기_신입사원_입문과정')
    """
    base_dir = Path(__file__).parent.parent.parent
    work_dir = base_dir / 'data' / work_folder

    if not work_dir.exists():
        print(f"작업 폴더가 존재하지 않습니다: {work_folder}")
        return

    processed_dir = work_dir / 'processed'
    results_dir = work_dir / 'results'

    csv_files = list(processed_dir.glob('*.csv'))

    if not csv_files:
        print(f"[{work_folder}] 분석할 CSV 파일이 없습니다.")
        return

    print(f"[{work_folder}] {len(csv_files)}개의 파일을 분석합니다.\n")

    success_count = 0
    for csv_file in csv_files:
        output_file = results_dir / (csv_file.stem + '_stats.json')

        if process_file(csv_file, output_file):
            print(f"\n  저장됨: {output_file.name}\n")
            success_count += 1
        else:
            print(f"  실패: {csv_file.name}\n")

    print(f"분석 완료: {success_count}/{len(csv_files)} 파일")


if __name__ == '__main__':
    process_all_files()
