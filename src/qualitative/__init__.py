"""
주관식(정성적) 데이터 통합 처리 모듈

- preprocess: 전처리 (맞춤법, 어미 통일, 무의미 응답 제거, 복합 응답 분리)
- integrate: 유사 응답 통합 및 대표 문장 생성
"""

from .preprocess import preprocess_responses
from .integrate import integrate_responses

__all__ = ['preprocess_responses', 'integrate_responses']
