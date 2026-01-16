"""
CSV 파일을 ANSI(CP949) 인코딩으로 변환하는 스크립트
"""

import os
import chardet
from pathlib import Path


def detect_encoding(file_path: str) -> str:
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def convert_to_ansi(input_path: str, output_path: str) -> bool:
    """
    파일을 ANSI(CP949) 인코딩으로 변환합니다.

    Args:
        input_path: 원본 파일 경로
        output_path: 출력 파일 경로

    Returns:
        성공 여부
    """
    try:
        # 원본 파일 인코딩 감지
        encoding = detect_encoding(input_path)
        print(f"  감지된 인코딩: {encoding}")

        # 파일 읽기
        with open(input_path, 'r', encoding=encoding) as f:
            content = f.read()

        # ANSI(CP949)로 저장
        with open(output_path, 'w', encoding='cp949', errors='replace') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"  오류 발생: {e}")
        return False


def process_all_files():
    """data/raw 폴더의 모든 CSV 파일을 변환합니다."""
    # 경로 설정
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    output_dir = base_dir / 'data' / 'output'

    # output 디렉토리 확인
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV 파일 목록
    csv_files = list(raw_dir.glob('*.csv'))

    if not csv_files:
        print("변환할 CSV 파일이 없습니다.")
        print(f"  원본 폴더: {raw_dir}")
        return

    print(f"총 {len(csv_files)}개의 파일을 변환합니다.\n")

    success_count = 0
    for csv_file in csv_files:
        output_file = output_dir / csv_file.name
        print(f"변환 중: {csv_file.name}")

        if convert_to_ansi(str(csv_file), str(output_file)):
            print(f"  완료: {output_file.name}\n")
            success_count += 1
        else:
            print(f"  실패: {csv_file.name}\n")

    print(f"\n변환 완료: {success_count}/{len(csv_files)} 파일")
    print(f"출력 폴더: {output_dir}")


if __name__ == '__main__':
    process_all_files()
