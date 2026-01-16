"""
분석 파이프라인 실행 스크립트

- 각 문항별 평균 계산
- 통계 결과 저장
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.calculate_stats import process_all_files as calculate_stats


def main():
    parser = argparse.ArgumentParser(description='분석 파이프라인 실행')
    parser.add_argument(
        'work_folder',
        help='작업 폴더명 (예: 2024_상반기_신입사원_입문과정)'
    )
    args = parser.parse_args()

    print("=" * 50)
    print("분석 시작")
    print(f"작업 폴더: {args.work_folder}")
    print("=" * 50)

    print("\n[1/1] 통계 계산 중...")
    calculate_stats(args.work_folder)

    print("\n분석 완료!")


if __name__ == '__main__':
    main()
