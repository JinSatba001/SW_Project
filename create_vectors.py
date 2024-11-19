import numpy as np
import pickle
from typing import Dict, List

def create_word_vectors(words: List[str], vector_size: int = 300) -> Dict[str, np.ndarray]:
    """
    한글 단어들의 벡터를 생성하는 함수
    
    Args:
        words: 벡터를 생성할 단어 리스트
        vector_size: 벡터의 차원 수 (기본값 300)
    
    Returns:
        단어:벡터 매핑 딕셔너리
    """
    # 랜덤 시드 설정으로 재현 가능성 확보
    np.random.seed(42)
    
    # 각 단어에 대한 랜덤 벡터 생성
    vectors = {}
    for word in words:
        # 랜덤 벡터 생성
        vector = np.random.randn(vector_size)
        # 정규화 (길이가 1인 벡터로 변환)
        vector = vector / np.linalg.norm(vector)
        vectors[word] = vector
    
    return vectors

def save_vectors(vectors: Dict[str, np.ndarray], filepath: str = 'data/vectors.pkl'):
    """벡터 데이터를 파일로 저장"""
    with open(filepath, 'wb') as f:
        pickle.dump(vectors, f)

def main():
    # 예시 단어 목록
    sample_words = [
        '사과', '배', '오렌지', '바나나', '포도',  # 과일
        '강아지', '고양이', '토끼', '말', '소',    # 동물
        '자동차', '비행기', '기차', '배', '버스',  # 교통수단
        '책상', '의자', '침대', '소파', '장롱',    # 가구
        '학교', '병원', '은행', '공원', '도서관',  # 건물
        '노래', '춤', '그림', '영화', '연극',      # 예술
        '축구', '야구', '농구', '배구', '탁구',    # 스포츠
        '봄', '여름', '가을', '겨울', '계절',      # 계절
        '아침', '점심', '저녁', '밤', '새벽',      # 시간
        '학생', '선생님', '의사', '경찰', '군인'   # 직업
    ]
    
    # 벡터 생성
    word_vectors = create_word_vectors(sample_words)
    
    # 벡터 저장
    save_vectors(word_vectors)
    
    # 테스트를 위한 유사도 계산
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    
    # 몇 가지 단어 쌍의 유사도 테스트
    test_pairs = [
        ('사과', '배'),       # 같은 카테고리 (과일)
        ('강아지', '고양이'), # 같은 카테고리 (동물)
        ('사과', '강아지'),   # 다른 카테고리
        ('학교', '학생'),     # 연관된 단어
        ('봄', '겨울'),       # 같은 카테고리 (계절)
    ]
    
    print("유사도 테스트 결과:")
    for word1, word2 in test_pairs:
        similarity = cosine_similarity(word_vectors[word1], word_vectors[word2])
        print(f"{word1} - {word2}: {similarity:.4f}")

if __name__ == '__main__':
    main()