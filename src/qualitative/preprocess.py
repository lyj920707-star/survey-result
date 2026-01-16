"""
주관식 응답 전처리 모듈

기능:
1. 무의미 응답 제거
2. 맞춤법 및 띄어쓰기 교정
3. 문장 어미 통일 (-했음/-함)
4. 복합 응답 분리 (명백히 다른 주제 2개 이상인 경우)
"""

import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import chardet


# 무의미 응답 패턴
MEANINGLESS_PATTERNS = [
    r'^[\s\-\_\.·,;:~!@#$%^&*()]*$',  # 공란, 특수문자만
    r'^없(음|다|습니다|어요|어)?\.?$',
    r'^(없|모름|글쎄|잘\s*모르겠|x|X|ㅇ|ㅁ)\.?$',
    r'^(특별히\s*)?없(음|다|습니다)?\.?$',
    r'^(딱히|별로)\s*없(음|다|습니다)?\.?$',
    r'^(해당\s*)?없(음)?\.?$',
    r'^(좋았습니다|좋음|좋다|굿|good|완벽|최고)\.?$',
    r'^없습니다\.?$',
    r'^잘\s*모르겠습니다\.?$',
    r'^\d+$',
]

# 띄어쓰기 교정 규칙
SPACING_RULES = [
    (r'할수있', '할 수 있'),
    (r'할수없', '할 수 없'),
    (r'될수있', '될 수 있'),
    (r'될수없', '될 수 없'),
    (r'있을수있', '있을 수 있'),
    (r'없을수있', '없을 수 있'),
    (r'것같', '것 같'),
    (r'수있', '수 있'),
    (r'수없', '수 없'),
    (r'너무좋', '너무 좋'),
    (r'정말좋', '정말 좋'),
    (r'매우좋', '매우 좋'),
    (r'도움이됐', '도움이 됐'),
    (r'도움이될', '도움이 될'),
    (r'에대해', '에 대해'),
    (r'에대한', '에 대한'),
    (r'(\S)할때', r'\1할 때'),
    (r'(\S)있을때', r'\1있을 때'),
]

# 오타 교정 규칙
TYPO_RULES = [
    (r'좋앗', '좋았'),
    (r'같앗', '같았'),
    (r'됬', '됐'),
    (r'됏', '됐'),
    (r'햇', '했'),
    (r'잇', '있'),
    (r'업슴', '없음'),
    (r'업습', '없습'),
    (r'갔습', '같습'),
    (r'것갔', '것 같'),
    (r'수잇', '수 있'),
]

# 어미 변환 규칙 - 문장 끝 (정규식 패턴, 대체 문자열)
ENDING_RULES = [
    # -습니다/-ㅂ니다 계열
    (r'했습니다\.?$', '했음'),
    (r'됐습니다\.?$', '됐음'),
    (r'였습니다\.?$', '였음'),
    (r'었습니다\.?$', '었음'),
    (r'습니다\.?$', '음'),
    (r'ㅂ니다\.?$', 'ㅁ'),

    # -어요/-아요 계열
    (r'했어요\.?$', '했음'),
    (r'됐어요\.?$', '됐음'),
    (r'었어요\.?$', '었음'),
    (r'았어요\.?$', '았음'),
    (r'여요\.?$', '임'),
    (r'어요\.?$', '음'),
    (r'아요\.?$', '음'),

    # -다/-ㄴ다 계열
    (r'했다\.?$', '했음'),
    (r'됐다\.?$', '됐음'),
    (r'었다\.?$', '었음'),
    (r'았다\.?$', '았음'),
    (r'인다\.?$', '임'),
    (r'ㄴ다\.?$', 'ㅁ'),
    (r'한다\.?$', '함'),
    (r'된다\.?$', '됨'),

    # -요 계열
    (r'해요\.?$', '함'),
    (r'돼요\.?$', '됨'),
    (r'네요\.?$', '네'),

    # 명사형 어미가 없는 경우 처리
    (r'할 수 있다\.?$', '할 수 있음'),
    (r'할 수 없다\.?$', '할 수 없음'),
    (r'될 것 같다\.?$', '될 것 같음'),
    (r'좋겠다\.?$', '좋겠음'),

    # 마침표 제거
    (r'\.$', ''),
]

# 문장 중간 어미 변환 규칙 (마침표 뒤 또는 문장 중간)
MID_SENTENCE_RULES = [
    # -습니다. → -음.
    (r'했습니다\.', '했음.'),
    (r'됐습니다\.', '됐음.'),
    (r'였습니다\.', '였음.'),
    (r'었습니다\.', '었음.'),
    (r'습니다\.', '음.'),
    (r'ㅂ니다\.', 'ㅁ.'),
    # -다. → -음.
    (r'했다\.', '했음.'),
    (r'됐다\.', '됐음.'),
    (r'었다\.', '었음.'),
    (r'았다\.', '았음.'),
]

# 복합 응답 분리 패턴 (명백히 다른 주제를 연결하는 접속사)
SPLIT_PATTERNS = [
    r',\s*그리고\s+',
    r'\.\s+그리고\s+',
    r',\s*또한\s+',
    r'\.\s+또한\s+',
]


def detect_encoding(file_path: Path) -> str:
    """파일의 인코딩을 감지합니다."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def is_meaningless(text: str) -> bool:
    """무의미한 응답인지 확인합니다."""
    if pd.isna(text):
        return True

    text = str(text).strip()

    if not text:
        return True

    for pattern in MEANINGLESS_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True

    return False


def fix_spacing(text: str) -> str:
    """띄어쓰기를 교정합니다."""
    if pd.isna(text):
        return text

    result = str(text)

    for pattern, replacement in SPACING_RULES:
        result = re.sub(pattern, replacement, result)

    # 다중 공백 정리
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def fix_typos(text: str) -> str:
    """흔한 오타를 교정합니다."""
    if pd.isna(text):
        return text

    result = str(text)

    for pattern, replacement in TYPO_RULES:
        result = re.sub(pattern, replacement, result)

    return result


def normalize_ending(text: str) -> str:
    """문장 어미를 '-했음/-함' 형식으로 통일합니다."""
    if pd.isna(text) or not text:
        return text

    result = str(text).strip()

    # 1. 문장 중간 어미 변환 먼저 적용 (마침표가 있는 경우)
    for pattern, replacement in MID_SENTENCE_RULES:
        result = re.sub(pattern, replacement, result)

    # 2. 문장 끝 어미 변환 적용
    for pattern, replacement in ENDING_RULES:
        result = re.sub(pattern, replacement, result)

    # 마침표로 끝나는 경우 제거
    if result.endswith('.'):
        result = result[:-1]

    return result


def should_split(text: str) -> bool:
    """복합 응답을 분리해야 하는지 확인합니다.

    분리 기준: 명백히 다른 주제 2가지 이상이 포함된 경우
    - "~했고, 강사님이~" (네트워킹 + 강사 역량)
    - "정보 교류~, 회고~" (정보 + 성찰)

    분리하지 않는 경우:
    - 원인-결과 관계
    - 주절-부연 설명 구조
    - 자기 이해 + 타인 이해 (같은 학습 경험)
    """
    if pd.isna(text) or not text:
        return False

    text = str(text).strip()

    # 분리 키워드 패턴
    # "~했고," 또는 "~었고," 뒤에 새로운 주제가 시작되는 경우
    split_indicator = re.search(
        r'(했고|었고|았고|였고|이고|하고)[,\s]+(강사|교수|선생|운영|진행|시설|장소|음식|식사)',
        text
    )

    if split_indicator:
        return True

    # 명백히 다른 주제를 나열하는 패턴
    different_topics = re.search(
        r'(좋았고|유익했고|도움됐고)[,\s]+(또한|그리고|추가로)',
        text
    )

    if different_topics:
        return True

    return False


def split_response(text: str) -> List[str]:
    """복합 응답을 분리합니다.

    분리 기준: 명백히 다른 주제가 "~했고," 등으로 연결된 경우
    """
    if pd.isna(text) or not text:
        return []

    text = str(text).strip()

    if not should_split(text):
        return [text]

    # "~했고, 강사님~" 패턴 분리
    parts = re.split(
        r'(했고|었고|았고|였고)[,\s]+(?=강사|교수|선생|운영|진행|시설|장소|음식|식사)',
        text
    )

    if len(parts) >= 2:
        results = []
        # 첫 번째 부분 + 어미
        first_part = parts[0].strip()
        if len(parts) > 1 and parts[1] in ['했고', '었고', '았고', '였고']:
            first_part += parts[1].replace('고', '음')
        results.append(first_part)

        # 나머지 부분들
        remaining = ''.join(parts[2:]).strip() if len(parts) > 2 else ''
        if remaining:
            results.append(remaining)

        return [r for r in results if r.strip()]

    return [text]


def preprocess_single(text: str) -> str:
    """단일 응답을 전처리합니다.

    처리 순서:
    1. 오타 교정
    2. 띄어쓰기 교정
    3. 어미 통일
    """
    if pd.isna(text):
        return ''

    result = str(text).strip()

    if not result:
        return ''

    # 1. 오타 교정
    result = fix_typos(result)

    # 2. 띄어쓰기 교정
    result = fix_spacing(result)

    # 3. 어미 통일
    result = normalize_ending(result)

    return result


def preprocess_responses(
    responses: List[str]
) -> Tuple[List[str], Dict]:
    """응답 리스트를 전처리합니다.

    Args:
        responses: 원본 응답 리스트

    Returns:
        (전처리된 응답 리스트, 통계 딕셔너리)
    """
    stats = {
        'original_count': len(responses),
        'removed_meaningless': 0,
        'split_count': 0,
        'final_count': 0,
    }

    processed = []

    for resp in responses:
        # 무의미 응답 제거
        if is_meaningless(resp):
            stats['removed_meaningless'] += 1
            continue

        # 전처리
        cleaned = preprocess_single(resp)

        if not cleaned:
            stats['removed_meaningless'] += 1
            continue

        # 복합 응답 분리
        parts = split_response(cleaned)

        if len(parts) > 1:
            stats['split_count'] += len(parts) - 1

        for part in parts:
            part_cleaned = preprocess_single(part)
            if part_cleaned and not is_meaningless(part_cleaned):
                processed.append(part_cleaned)

    stats['final_count'] = len(processed)

    return processed, stats


def is_qualitative_column(series: pd.Series) -> bool:
    """해당 컬럼이 주관식(서술형) 컬럼인지 확인합니다."""
    non_empty = series.dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != '']

    if len(non_empty) == 0:
        return False

    # 모든 값이 숫자인 경우 제외
    numeric_count = non_empty.str.match(r'^\d+\.?\d*$').sum()
    if numeric_count == len(non_empty):
        return False

    # 리커트 척도 값인 경우 제외
    likert_values = {'매우 그렇다', '그렇다', '보통이다', '그렇지 않다', '매우 그렇지 않다', '1', '2', '3', '4', '5'}
    unique_values = set(non_empty.unique())
    if unique_values.issubset(likert_values):
        return False

    # 평균 문자열 길이가 2자 이상이면 주관식으로 판단
    avg_length = non_empty.str.len().mean()
    return avg_length > 2


if __name__ == '__main__':
    # 테스트
    test_responses = [
        "좋았습니다",
        "너무 유익했습니다.",
        "소통할수있는부분이 좋았습니다",
        "없음",
        "",
        "서로 알아가는 시간이어서 너무 좋았고, 강사님이 잘 이끌어 주었다",
        "나에 대해서 더 잘 알 수 있었고, 구성원들을 이해하는 데에도 도움이 되었다",
    ]

    processed, stats = preprocess_responses(test_responses)

    print("=== 전처리 결과 ===")
    for p in processed:
        print(f"  - {p}")
    print(f"\n통계: {stats}")
