import random
from pathlib import Path

def load_words(filename):
    """단어 목록을 로드합니다."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Error loading words from {filename}: {e}")
        return []

class WordManager:
    def __init__(self):
        # 정답 단어 목록과 유효한 추측 단어 목록을 로드
        self.secret_words = load_words('data/secrets.txt')
        self.valid_words = set(load_words('data/frequent_words.txt'))
        
        # 현재 게임 상태 초기화
        self.current_word = None
        self.current_game_id = 0
    
    def get_random_word(self):
        """게임에 사용할 랜덤 단어를 선택합니다."""
        self.current_word = random.choice(self.secret_words)
        self.current_game_id += 1
        return self.current_word
    
    def is_valid_word(self, word):
        """입력된 단어가 유효한 단어인지 확인합니다."""
        return word in self.valid_words
    
    def calculate_similarity(self, word1, word2):
        """두 단어의 유사도를 계산합니다.
        완전히 같은 단어면 1.0, 다른 단어면 0.0을 반환합니다."""
        try:
            # 기본적인 일치 여부 검사
            if word1 == word2:
                return 1.0
                
            # 한글 자모 분리 후 유사도 계산
            # 여기서는 간단히 구현했지만, 필요하다면 더 정교한 유사도 계산 로직을 추가할 수 있습니다
            common_chars = set(word1) & set(word2)
            total_chars = set(word1) | set(word2)
            
            if not total_chars:
                return 0.0
                
            return len(common_chars) / len(total_chars)
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

# 싱글톤 인스턴스 생성
word_manager = WordManager()

def get_random_word():
    """랜덤 단어를 반환합니다."""
    return word_manager.get_random_word()

def calculate_similarity(word1, word2):
    """두 단어의 유사도를 계산합니다."""
    return word_manager.calculate_similarity(word1, word2)

def is_valid_word(word):
    """단어가 유효한지 확인합니다."""
    return word_manager.is_valid_word(word)