import numpy as np
from numpy import dot
from numpy.linalg import norm
import random

def get_random_word():
    try:
        with open('data/secrets.txt', 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f.readlines()]
            return random.choice(words)
    except:
        return "기본"
    

def similarity(word1: str, word2: str) -> float:
    if word1 == word2:
        return 1.0
    
    # 문자 기반 유사도 계산
    char_similarity = calculate_char_similarity(word1, word2)
    
    # 기본 벡터 유사도 계산
    vec1 = create_vector(word1)
    vec2 = create_vector(word2)
    vector_similarity = dot(vec1, vec2) / (norm(vec1) * norm(vec2))
    
    # 최종 유사도 = 문자 유사도 40% + 벡터 유사도 60%
    final_similarity = (0.4 * char_similarity + 0.6 * vector_similarity)
    
    # 유사도가 0.3 미만이면 더 낮게 조정
    if final_similarity < 0.3:
        final_similarity *= 0.5
    
    return float(max(0, min(1.0, final_similarity)))

def calculate_char_similarity(word1: str, word2: str) -> float:
    def decompose(char):
        if '가' <= char <= '힣':
            code = ord(char) - ord('가')
            jong = code % 28
            jung = ((code - jong) // 28) % 21
            cho = ((code - jong) // 28) // 21
            return cho, jung, jong
        return None
    
    min_len = min(len(word1), len(word2))
    total = 0
    
    for c1, c2 in zip(word1[:min_len], word2[:min_len]):
        d1, d2 = decompose(c1), decompose(c2)
        if d1 and d2:
            total += sum(1 for x, y in zip(d1, d2) if x == y) / 3
    
    return total / max(len(word1), len(word2))

def create_vector(word: str) -> np.ndarray:
    """단어를 벡터로 변환"""
    random.seed(hash(word))
    vec = np.array([random.random() for _ in range(100)])
    return vec / norm(vec)