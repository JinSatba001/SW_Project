import numpy as np
import pickle
import random
from create_vectors import create_word_vectors

def get_random_word():
    with open('data/secrets.txt', 'r', encoding='utf-8') as f:
        words = f.readlines()
    return random.choice(words).strip()

def calculate_similarity(word1, word2):
    try:
        with open('data/vectors.pkl', 'rb') as f:
            vectors = pickle.load(f)

        """
        기존 벡터에 없는 단어 처리 (유사도 0.0으로 반환)
        if word1 not in vectors or word2 not in vectors:
            return 0.0        
        """

        # 벡터에 없는 단어 처리
        if word1 not in vectors:
            vectors[word1] = create_word_vectors([word1])
        if word2 not in vectors:
            vectors[word2] = create_word_vectors([word2])
        
        vec1 = vectors[word1]
        vec2 = vectors[word2]
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)
    
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0
