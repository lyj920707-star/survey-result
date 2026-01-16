"""
주관식 응답 통합 모듈

기능:
1. 키워드 기반 그룹핑
2. 의미 유사도 기반 통합
3. 대표 문장 선택 (가장 구체적이고 완전한 문장)
4. 공통의견 수 표기

작업 원칙:
- 원문을 최대한 보존
- 의미 축소/손실 금지
- 가장 구체적인 문장을 대표 문장으로 선택
- 단일 응답은 (공통의견 n) 표기 생략
"""

import re
from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher
from collections import defaultdict


# 주제별 키워드 그룹 정의
KEYWORD_GROUPS = {
    '소통_대화': ['소통', '대화', '경청', '커뮤니케이션', '의사소통', '말하', '듣', '경청'],
    '자기이해_성찰': ['자기', '나를', '나에 대해', '자신', '성찰', '되돌아', '돌아보', '반성', '깨달'],
    '타인이해_공감': ['타인', '상대방', '이해', '공감', '배려', '존중', '다름', '차이'],
    '네트워킹_친목': ['네트워킹', '친목', '교류', '인맥', '만남', '친해', '알게', '동기', '식구', '가족사'],
    '협업_팀워크': ['협업', '팀워크', '협동', '팀', '함께', '시너지', '조직'],
    '목표_계획': ['목표', '계획', '비전', '방향', '만다라트', '만다르트', '설정'],
    '스피치_발표': ['스피치', '스피킹', '발표', '프레젠테이션', '말하기', '표현', '비즈니스 스피치'],
    'MBTI_성격': ['mbti', 'mnti', '성격', '유형', '성향'],
    '강사_진행': ['강사', '교수', '선생', '진행', '운영', '설명'],
    '실무_현업': ['실무', '현업', '업무', '일', '적용', '활용'],
    '가족사_이해': ['가족사', '양돈', '사료', '산업', '견학'],
}

# 동의어 그룹 (같은 의미로 취급)
SYNONYM_GROUPS = [
    ['mbti', 'mnti', 'MBTI', 'MNTI'],
    ['스피치', '스피킹', '말하기', '비즈니스 스피치', '스피치교육', '스피킹과목'],
    ['만다라트', '만다르트', 'mandal-art', 'mandalart'],
    ['가족사', '이지가족', '이기가족', '이지가족사'],
    ['양돈', '양돈산업', '양돈 산업'],
    ['목표', '목표설정', '목표 설정', '목표수립', '목표 수립'],
    ['협동', '협동심', '팀워크', '협업'],
    ['견학', '현장견학', '현장 견학'],
]

# 불용어 (키워드 추출 시 제외)
STOPWORDS = {
    '이', '가', '을', '를', '은', '는', '에', '에서', '으로', '로',
    '와', '과', '의', '도', '만', '부터', '까지', '에게', '한테',
    '하다', '되다', '있다', '없다', '같다', '하고', '해서', '하면',
    '그', '저', '이런', '저런', '그런', '어떤', '무슨',
    '것', '수', '등', '때', '중', '후', '전', '점', '면',
    '너무', '매우', '아주', '정말', '진짜', '많이', '잘', '더',
    '좋다', '좋았다', '좋음', '유익하다', '유익했다', '도움이', '됐다', '됐음',
    '했음', '했다', '됨', '함', '있음', '없음',
}


def extract_keywords(text: str) -> Set[str]:
    """텍스트에서 핵심 키워드를 추출합니다."""
    if not text:
        return set()

    # 정규화
    normalized = text.lower().strip()
    normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)

    # 단어 분리 (2글자 이상)
    words = set(w for w in normalized.split() if len(w) >= 2)

    # 불용어 제거
    keywords = words - STOPWORDS

    return keywords


def get_topic_group(text: str) -> List[str]:
    """텍스트가 속하는 주제 그룹을 반환합니다."""
    text_lower = text.lower()
    matched_groups = []

    for group_name, keywords in KEYWORD_GROUPS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched_groups.append(group_name)
                break

    return matched_groups


def are_synonyms(text1: str, text2: str) -> bool:
    """두 텍스트가 동의어 관계인지 확인합니다."""
    text1_lower = text1.lower().strip()
    text2_lower = text2.lower().strip()

    for synonyms in SYNONYM_GROUPS:
        synonyms_lower = [s.lower() for s in synonyms]
        match1 = any(syn in text1_lower for syn in synonyms_lower)
        match2 = any(syn in text2_lower for syn in synonyms_lower)
        if match1 and match2:
            return True

    return False


def is_short_response(text: str) -> bool:
    """짧은 응답(단어 수준)인지 확인합니다."""
    # 공백 제거 후 길이가 15자 이하면 짧은 응답
    clean = re.sub(r'\s+', '', text)
    return len(clean) <= 15


def short_contained_in_long(short: str, long: str) -> bool:
    """짧은 응답의 핵심 키워드가 긴 응답에 포함되는지 확인합니다."""
    short_lower = short.lower()
    long_lower = long.lower()

    # 짧은 응답 자체가 포함되면 True
    if short_lower in long_lower:
        return True

    # 동의어 확인
    if are_synonyms(short, long):
        return True

    # 짧은 응답의 키워드가 긴 응답에 있는지
    short_keywords = extract_keywords(short)
    if short_keywords:
        long_keywords = extract_keywords(long)
        # 짧은 응답의 모든 키워드가 긴 응답에 포함되면 True
        if short_keywords.issubset(long_keywords):
            return True
        # 동의어 그룹 고려
        for syn_group in SYNONYM_GROUPS:
            syn_lower = [s.lower() for s in syn_group]
            short_has_syn = any(s in short_lower for s in syn_lower)
            long_has_syn = any(s in long_lower for s in syn_lower)
            if short_has_syn and long_has_syn:
                return True

    return False


def calculate_similarity(text1: str, text2: str) -> float:
    """두 텍스트의 유사도를 계산합니다 (0~1)."""
    if not text1 or not text2:
        return 0.0

    # 정규화
    norm1 = re.sub(r'[^\w\s가-힣]', '', text1.lower())
    norm2 = re.sub(r'[^\w\s가-힣]', '', text2.lower())

    if norm1 == norm2:
        return 1.0

    # 키워드 기반 유사도
    kw1 = extract_keywords(text1)
    kw2 = extract_keywords(text2)

    if not kw1 or not kw2:
        return 0.0

    # Jaccard 유사도
    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    keyword_sim = intersection / union if union > 0 else 0

    # 문자열 유사도
    string_sim = SequenceMatcher(None, norm1, norm2).ratio()

    # 가중 평균 (키워드 60%, 문자열 40%)
    return keyword_sim * 0.6 + string_sim * 0.4


def select_representative(responses: List[str]) -> str:
    """통합된 응답 중 대표 문장을 선택합니다.

    선택 기준:
    1. 가장 구체적이고 완전한 문장
    2. 길이가 적절한 문장 (너무 짧지 않은)
    3. 문장 구조가 완전한 것
    """
    if not responses:
        return ''

    if len(responses) == 1:
        return responses[0]

    # 점수 계산
    scored = []
    for resp in responses:
        score = 0

        # 길이 점수 (너무 짧거나 너무 긴 것은 감점)
        length = len(resp)
        if 10 <= length <= 100:
            score += 30
        elif length > 100:
            score += 20
        elif length >= 5:
            score += 10

        # 키워드 다양성 점수
        keywords = extract_keywords(resp)
        score += len(keywords) * 5

        # 문장 완결성 점수 (어미가 있으면)
        if re.search(r'(음|함|됨|임)$', resp):
            score += 10

        # 구체적 표현 점수
        concrete_patterns = ['통해', '배울', '알게', '이해', '향상', '느낌', '느낌', '경험']
        for pattern in concrete_patterns:
            if pattern in resp:
                score += 5

        scored.append((resp, score))

    # 점수 높은 순 정렬
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0]


def should_merge(resp1: str, resp2: str, threshold: float = 0.4) -> bool:
    """두 응답을 통합해야 하는지 판단합니다.

    통합 기준:
    - 동일한 주제 그룹에 속함
    - 유사도가 임계값 이상
    - 핵심 키워드가 겹침
    - 동의어 관계
    - 짧은 응답이 긴 응답에 포함됨
    """
    # 1. 동의어 관계 확인 (가장 먼저)
    if are_synonyms(resp1, resp2):
        return True

    # 2. 짧은 응답이 긴 응답에 포함되는지 확인
    if is_short_response(resp1) and not is_short_response(resp2):
        if short_contained_in_long(resp1, resp2):
            return True
    elif is_short_response(resp2) and not is_short_response(resp1):
        if short_contained_in_long(resp2, resp1):
            return True
    elif is_short_response(resp1) and is_short_response(resp2):
        # 둘 다 짧은 응답이면 동의어/유사도 기반 통합
        if are_synonyms(resp1, resp2):
            return True

    # 3. 주제 그룹 확인
    groups1 = set(get_topic_group(resp1))
    groups2 = set(get_topic_group(resp2))

    # 동일 주제 그룹에 속하면 통합 가능성 높음
    if groups1 & groups2:
        threshold = 0.25  # 임계값 더 낮춤

    # 4. 유사도 계산
    similarity = calculate_similarity(resp1, resp2)

    if similarity >= threshold:
        return True

    # 5. 키워드 겹침 확인
    kw1 = extract_keywords(resp1)
    kw2 = extract_keywords(resp2)

    # 핵심 키워드가 1개 이상 겹치고, 같은 주제 그룹이면 통합
    common = kw1 & kw2
    if len(common) >= 1 and (groups1 & groups2):
        return True

    # 핵심 키워드가 2개 이상 겹치면 통합
    if len(common) >= 2:
        return True

    return False


def integrate_responses(
    responses: List[str],
    similarity_threshold: float = 0.4
) -> List[Dict]:
    """응답들을 통합하여 대표 문장 리스트를 생성합니다.

    Args:
        responses: 전처리된 응답 리스트
        similarity_threshold: 유사도 임계값

    Returns:
        통합된 결과 리스트
        [{'representative': '대표문장', 'count': n, 'sources': [원본들]}, ...]
    """
    if not responses:
        return []

    # 중복 제거 (정확히 동일한 응답)
    unique_responses = list(dict.fromkeys(responses))

    # 그룹 초기화
    groups = []
    used = set()

    # 주제별로 먼저 그룹핑
    topic_groups = defaultdict(list)
    no_topic = []

    for i, resp in enumerate(unique_responses):
        topics = get_topic_group(resp)
        if topics:
            for topic in topics:
                topic_groups[topic].append((i, resp))
        else:
            no_topic.append((i, resp))

    # 주제 그룹 내에서 통합
    for topic, items in topic_groups.items():
        for i, resp in items:
            if i in used:
                continue

            group = {
                'sources': [resp],
                'indices': [i],
            }
            used.add(i)

            # 같은 주제 내에서 유사한 응답 찾기
            for j, other in items:
                if j in used:
                    continue

                if should_merge(resp, other, similarity_threshold):
                    group['sources'].append(other)
                    group['indices'].append(j)
                    used.add(j)

            groups.append(group)

    # 주제 없는 응답 처리
    for i, resp in no_topic:
        if i in used:
            continue

        group = {
            'sources': [resp],
            'indices': [i],
        }
        used.add(i)

        # 다른 주제 없는 응답과 통합 시도
        for j, other in no_topic:
            if j in used:
                continue

            if should_merge(resp, other, similarity_threshold):
                group['sources'].append(other)
                group['indices'].append(j)
                used.add(j)

        groups.append(group)

    # 그룹 간 추가 통합 시도 (2차 통합)
    merged_groups = []
    group_used = set()

    for i, group1 in enumerate(groups):
        if i in group_used:
            continue

        merged = group1.copy()
        merged['sources'] = list(group1['sources'])

        for j, group2 in enumerate(groups):
            if j <= i or j in group_used:
                continue

            # 대표 문장 간 유사도 확인
            rep1 = select_representative(group1['sources'])
            rep2 = select_representative(group2['sources'])

            if should_merge(rep1, rep2, similarity_threshold + 0.1):
                merged['sources'].extend(group2['sources'])
                group_used.add(j)

        group_used.add(i)
        merged_groups.append(merged)

    # 최종 결과 생성
    results = []
    for group in merged_groups:
        representative = select_representative(group['sources'])
        count = len(group['sources'])

        # 공통의견 표기 (2개 이상일 때만)
        if count >= 2:
            display = f"{representative} (공통의견 {count})"
        else:
            display = representative

        results.append({
            'representative': representative,
            'display': display,
            'count': count,
            'sources': group['sources'],
        })

    # 빈도순 정렬 (높은 순)
    results.sort(key=lambda x: (-x['count'], -len(x['representative'])))

    return results


def format_output(results: List[Dict]) -> List[str]:
    """결과를 출력용 문자열 리스트로 변환합니다."""
    return [r['display'] for r in results]


if __name__ == '__main__':
    # 테스트
    test_responses = [
        "소통 유형을 점검하고 상대방에 대한 이해도가 높아졌음",
        "의사소통할 때 나 스스로의 모습을 돌아볼 수 있었음",
        "다른 가족사 식구들을 만날 수 있고 서로의 현업에 대해 이야기할 수 있었음",
        "인맥",
        "대화 기술 강의",
        "대화의 방법",
        "MBTI가 유익했음",
        "목표 설정 방법을 배웠음",
    ]

    results = integrate_responses(test_responses)

    print("=== 통합 결과 ===")
    for r in results:
        print(f"  - {r['display']}")
        if r['count'] > 1:
            print(f"    원본: {r['sources']}")
