import numpy as np
import pickle
import random

def get_random_word():
    with open('data/secrets.txt', 'r', encoding='utf-8') as f:
        words = f.readlines()
    return random.choice(words).strip()

def calculate_similarity(word1, word2):
    try:
        with open('data/vectors.pkl', 'rb') as f:
            vectors = pickle.load(f)
        
        if word1 not in vectors or word2 not in vectors:
            return 0.0
            
        vec1 = vectors[word1]
        vec2 = vectors[word2]
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0