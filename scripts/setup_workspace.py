"""
Inbound 폴더의 파일을 자동으로 처리하여 data 폴더 구조를 생성하는 스크립트

동작 방식:
1. inbound/ 폴더의 모든 파일 스캔
2. 파일명(확장자 제외)을 폴더명으로 사용하여 data/{파일명}/ 구조 생성
3. 하위 폴더 생성: raw, processed, results, output, qualitative
4. 원본 파일을 data/{파일명}/raw/로 이동
5. 기존 폴더가 있으면 삭제 후 재생성
"""

import argparse
import sys
import shutil
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def process_file(file_path: Path, data_dir: Path, dry_run: bool = False, no_delete: bool = False) -> bool:
    """
    개별 파일을 처리하여 작업 폴더 구조를 생성하고 파일을 이동합니다.

    Args:
        file_path: 처리할 파일 경로
        data_dir: data 폴더 경로
        dry_run: True이면 실제 작업을 수행하지 않고 시뮬레이션만 수행
        no_delete: True이면 기존 폴더가 있을 때 건너뜀

    Returns:
        성공 여부
    """
    try:
        # 파일명(확장자 제외)을 작업 폴더명으로 사용
        work_folder_name = file_path.stem
        work_folder = data_dir / work_folder_name

        print(f"  파일명: {file_path.name}")
        print(f"  작업 폴더: {work_folder_name}")

        # 기존 폴더 처리
        if work_folder.exists():
            if no_delete:
                print(f"  건너뜀: {work_folder_name} 폴더가 이미 존재합니다.")
                return False

            print(f"  경고: {work_folder_name} 폴더가 이미 존재합니다. 삭제합니다.")
            if not dry_run:
                shutil.rmtree(work_folder)

        # 폴더 구조 생성
        subfolders = ['raw', 'processed', 'results', 'output', 'qualitative']

        if not dry_run:
            work_folder.mkdir(parents=True, exist_ok=True)
            for subfolder in subfolders:
                (work_folder / subfolder).mkdir(exist_ok=True)

        print(f"  폴더 생성: data/{work_folder_name}/")
        print(f"  하위 폴더 생성 완료: {', '.join(subfolders)}")

        # 파일 이동
        destination = work_folder / 'raw' / file_path.name
        print(f"  파일 이동: inbound/{file_path.name} → data/{work_folder_name}/raw/{file_path.name}")

        if not dry_run:
            shutil.move(str(file_path), str(destination))

        print(f"  [완료]")
        return True

    except Exception as e:
        print(f"  [오류] {e}")
        return False


def process_all_files(inbound_dir: Path, data_dir: Path, dry_run: bool = False,
                      no_delete: bool = False, specific_files: list = None) -> tuple:
    """
    inbound 폴더의 모든 파일을 처리합니다.

    Args:
        inbound_dir: inbound 폴더 경로
        data_dir: data 폴더 경로
        dry_run: True이면 실제 작업을 수행하지 않고 시뮬레이션만 수행
        no_delete: True이면 기존 폴더가 있을 때 건너뜀
        specific_files: 특정 파일명 리스트 (None이면 모든 파일 처리)

    Returns:
        (성공 개수, 전체 파일 개수) 튜플
    """
    # inbound 폴더 확인 및 생성
    if not inbound_dir.exists():
        print(f"inbound 폴더가 존재하지 않습니다. 생성합니다: {inbound_dir}")
        if not dry_run:
            inbound_dir.mkdir(parents=True, exist_ok=True)
        return (0, 0)

    # 파일 목록 조회
    if specific_files:
        # 특정 파일만 처리
        files = [inbound_dir / f for f in specific_files if (inbound_dir / f).exists()]
        not_found = [f for f in specific_files if not (inbound_dir / f).exists()]
        if not_found:
            print(f"경고: 다음 파일을 찾을 수 없습니다: {', '.join(not_found)}")
    else:
        # 모든 파일 처리 (하위 디렉토리 및 .gitkeep 파일 제외)
        files = [f for f in inbound_dir.iterdir() if f.is_file() and f.name != '.gitkeep']

    if not files:
        print("처리할 파일이 없습니다.")
        return (0, 0)

    print(f"\n발견된 파일: {len(files)}개")
    for f in files:
        print(f"  - {f.name}")
    print()

    # 파일 처리
    success_count = 0
    for idx, file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] {file.name} 처리 중...")
        if process_file(file, data_dir, dry_run, no_delete):
            success_count += 1
        print()

    return (success_count, len(files))


def main():
    parser = argparse.ArgumentParser(
        description='Inbound 폴더의 파일을 자동으로 처리하여 작업 폴더 구조를 생성합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 모든 파일 처리
  python scripts/setup_workspace.py

  # 특정 파일만 처리
  python scripts/setup_workspace.py 2024_상반기.csv 2025_하반기.xlsx

  # 시뮬레이션 모드 (실제 작업 없이 확인만)
  python scripts/setup_workspace.py --dry-run

  # 기존 폴더가 있으면 건너뛰기
  python scripts/setup_workspace.py --no-delete
        """
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='처리할 파일명 (지정하지 않으면 모든 파일 처리)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 작업을 수행하지 않고 시뮬레이션만 수행'
    )
    parser.add_argument(
        '--no-delete',
        action='store_true',
        help='기존 폴더가 있으면 삭제하지 않고 건너뜀'
    )
    args = parser.parse_args()

    # 경로 설정
    inbound_dir = project_root / 'inbound'
    data_dir = project_root / 'data'

    # 헤더 출력
    print("=" * 50)
    if args.dry_run:
        print("Inbound 파일 자동 처리 (시뮬레이션 모드)")
    else:
        print("Inbound 파일 자동 처리 시작")
    print("=" * 50)

    # 파일 처리
    success_count, total_count = process_all_files(
        inbound_dir,
        data_dir,
        dry_run=args.dry_run,
        no_delete=args.no_delete,
        specific_files=args.files if args.files else None
    )

    # 결과 출력
    print("=" * 50)
    if args.dry_run:
        print(f"시뮬레이션 완료: {success_count}/{total_count} 파일")
    else:
        print(f"처리 완료: {success_count}/{total_count} 파일 성공")
    print("=" * 50)

    # 다음 단계 안내
    if success_count > 0 and not args.dry_run:
        print("\n다음 단계:")

        # 처리된 폴더명 목록 생성
        if args.files:
            work_folders = [Path(f).stem for f in args.files]
        else:
            # inbound에서 처리된 모든 파일의 폴더명 추정
            work_folders = []
            for item in data_dir.iterdir():
                if item.is_dir() and (item / 'raw').exists():
                    # raw 폴더에 파일이 있는지 확인
                    if list((item / 'raw').glob('*')):
                        work_folders.append(item.name)

        for folder in work_folders:
            print(f"  python scripts/run_all.py {folder}")


if __name__ == '__main__':
    main()
