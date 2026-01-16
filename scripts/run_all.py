"""
전체 파이프라인 실행 스크립트 sd;lkfjas;ddkfj;ls

1. 전처리: 리커트 척도 → 숫자 변환
2. 분석: 문항별 평균 계산
3. 리포팅: 템플릿에 결과 입력
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing.convert_likert import process_all_files as convert_likert
from src.analysis.calculate_stats import process_all_files as calculate_stats
from src.reporting.fill_template import process_all_results as fill_template


def main():
    parser = argparse.ArgumentParser(description='전체 파이프라인 실행')
    parser.add_argument(
        'work_folder',
        help='작업 폴더명 (예: 2024_상반기_신입사원_입문과정)'
    )
    args = parser.parse_args()

    print("=" * 50)
    print("설문 결과 처리 파이프라인")
    print(f"작업 폴더: {args.work_folder}")
    print("=" * 50)

    # 1단계: 전처리
    print("\n[1/3] 전처리: 리커트 척도 변환 중...")
    convert_likert(args.work_folder)

    # 2단계: 분석
    print("\n[2/3] 분석: 통계 계산 중...")
    calculate_stats(args.work_folder)

    # 3단계: 리포팅
    print("\n[3/3] 리포팅: 템플릿 작성 중...")
    fill_template(args.work_folder)

    print("\n" + "=" * 50)
    print("모든 처리 완료!")
    print("=" * 50)


if __name__ == '__main__':
    main()
