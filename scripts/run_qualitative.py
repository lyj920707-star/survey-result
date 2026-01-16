"""
주관식(정성적) 데이터 통합 처리 파이프라인

처리 단계:
1. 전처리 (맞춤법, 어미 통일, 무의미 응답 제거)
2. 복합 응답 분리 (명백히 다른 주제 2개 이상인 경우)
3. 유사 응답 통합 및 대표 문장 생성
4. 결과 출력 (CSV, Excel)
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import chardet

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.qualitative.preprocess import preprocess_responses, is_qualitative_column
from src.qualitative.integrate import integrate_responses, format_output


def detect_encoding(file_path: Path) -> str:
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def process_file(
    input_path: Path,
    output_dir: Path,
    similarity_threshold: float = 0.4
) -> dict:
    """단일 CSV 파일을 처리합니다."""
    # 파일 읽기
    encoding = detect_encoding(input_path)
    df = pd.read_csv(input_path, encoding=encoding)

    results = {
        'file': input_path.name,
        'total_rows': len(df),
        'questions': {},
    }

    # 주관식 컬럼 식별
    qualitative_cols = []
    for col in df.columns:
        if is_qualitative_column(df[col]):
            # 타임스탬프, 법인 선택 등 제외
            col_lower = col.lower()
            if any(skip in col_lower for skip in ['타임스탬프', '법인', '소속', 'timestamp']):
                continue
            qualitative_cols.append(col)

    if not qualitative_cols:
        print("  주관식 컬럼을 찾을 수 없습니다.")
        return results

    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    # Excel 출력용 데이터
    excel_sheets = {}

    for col in qualitative_cols:
        print(f"\n  처리 중: {col[:50]}...")

        # 응답 추출
        responses = df[col].dropna().astype(str).str.strip().tolist()
        responses = [r for r in responses if r]

        if not responses:
            continue

        # 1단계: 전처리
        preprocessed, prep_stats = preprocess_responses(responses)

        print(f"    원본: {prep_stats['original_count']}개")
        print(f"    제거: {prep_stats['removed_meaningless']}개 (무의미 응답)")
        if prep_stats['split_count'] > 0:
            print(f"    분리: {prep_stats['split_count']}개 (복합 응답)")
        print(f"    유효: {prep_stats['final_count']}개")

        if not preprocessed:
            continue

        # 2단계: 통합
        integrated = integrate_responses(preprocessed, similarity_threshold)

        print(f"    통합 후: {len(integrated)}개 항목")

        # 통합 비율 확인
        if len(preprocessed) > 0:
            ratio = len(integrated) / len(preprocessed)
            if ratio < 0.25:
                print(f"    [주의] 과도한 통합 (재검토 권장)")
            elif ratio > 0.9:
                print(f"    [주의] 통합 부족 (재검토 권장)")

        # 결과 저장
        question_short = col[:50] + '...' if len(col) > 50 else col

        results['questions'][question_short] = {
            'full_question': col,
            'original_count': prep_stats['original_count'],
            'removed_count': prep_stats['removed_meaningless'],
            'valid_count': prep_stats['final_count'],
            'integrated_count': len(integrated),
            'items': integrated,
        }

        # Excel 시트 데이터
        sheet_data = []
        for item in integrated:
            sheet_data.append({
                '통합 결과': item['display'],
                '빈도': item['count'],
                '원본 응답': ' | '.join(item['sources']) if item['count'] > 1 else '',
            })

        # 시트명 정리 (31자 제한, 특수문자 제거)
        import re
        safe_name = re.sub(r'[\\/*?:\[\]]', '', question_short)[:31]
        excel_sheets[safe_name] = pd.DataFrame(sheet_data)

    # Excel 파일 저장
    excel_path = output_dir / f"{input_path.stem}_통합결과.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 요약 시트
        summary_data = []
        for q_name, q_data in results['questions'].items():
            summary_data.append({
                '질문': q_data['full_question'],
                '원본 응답수': q_data['original_count'],
                '제거된 응답수': q_data['removed_count'],
                '유효 응답수': q_data['valid_count'],
                '통합 후 항목수': q_data['integrated_count'],
            })

        if summary_data:
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='요약', index=False)

        # 각 질문별 시트
        for sheet_name, sheet_df in excel_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n  Excel 저장: {excel_path.name}")

    # CSV 파일 저장 (통합 결과만)
    csv_path = output_dir / f"{input_path.stem}_통합결과.csv"
    all_items = []
    for q_name, q_data in results['questions'].items():
        for item in q_data['items']:
            all_items.append({
                '질문': q_data['full_question'],
                '통합 결과': item['display'],
                '빈도': item['count'],
            })

    if all_items:
        pd.DataFrame(all_items).to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"  CSV 저장: {csv_path.name}")

    # JSON 파일 저장 (상세 결과)
    json_path = output_dir / f"{input_path.stem}_통합결과.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  JSON 저장: {json_path.name}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='주관식 데이터 통합 처리',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python run_qualitative.py 2024_상반기_신입사원_입문과정
  python run_qualitative.py 2024_상반기_신입사원_입문과정 --threshold 0.5
        """
    )
    parser.add_argument(
        'work_folder',
        help='작업 폴더명 (예: 2024_상반기_신입사원_입문과정)'
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.4,
        help='유사도 임계값 (0.0~1.0, 기본값: 0.4)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("주관식 데이터 통합 처리")
    print("=" * 60)
    print(f"작업 폴더: {args.work_folder}")
    print(f"유사도 임계값: {args.threshold}")

    # 작업 폴더 확인
    base_dir = Path(__file__).parent.parent
    work_dir = base_dir / 'data' / args.work_folder

    if not work_dir.exists():
        print(f"\n오류: 작업 폴더가 존재하지 않습니다: {args.work_folder}")
        sys.exit(1)

    # 입력 디렉토리 (processed 폴더)
    input_dir = work_dir / 'processed'
    if not input_dir.exists():
        print(f"\n오류: processed 폴더가 없습니다: {input_dir}")
        sys.exit(1)

    # 출력 디렉토리
    output_dir = work_dir / 'qualitative'

    # CSV 파일 처리
    csv_files = list(input_dir.glob('*.csv'))

    if not csv_files:
        print(f"\n처리할 CSV 파일이 없습니다.")
        sys.exit(1)

    print(f"\n{len(csv_files)}개 파일 처리 시작\n")
    print("=" * 60)

    all_results = []

    for csv_file in csv_files:
        print(f"\n파일: {csv_file.name}")
        print("-" * 40)

        result = process_file(csv_file, output_dir, args.threshold)
        all_results.append(result)

    # 최종 요약
    print("\n" + "=" * 60)
    print("처리 완료!")
    print("=" * 60)

    total_questions = sum(len(r['questions']) for r in all_results)
    total_items = sum(
        sum(q['integrated_count'] for q in r['questions'].values())
        for r in all_results
    )

    print(f"\n처리된 질문: {total_questions}개")
    print(f"통합된 항목: {total_items}개")
    print(f"\n출력 위치: {output_dir}")


if __name__ == '__main__':
    main()
