# backend/app/services/word_similarity.py
from gensim.models import Word2Vec
from konlpy.tag import Okt
import numpy as np

class WordSimilarityService:
    def __init__(self):
        # Okt 형태소 분석기 초기화
        self.okt = Okt()
        
        # 간단한 예시 문장들로 모델 학습
        sentences = [
            "사과 바나나 오렌지 과일이 맛있다",
            "강아지 고양이 동물을 좋아한다",
            "책 공부 학교 교육이 중요하다",
            "자동차 버스 기차 교통수단을 이용한다",
            # 더 많은 예시 문장 추가...
        ]
        
        # 문장을 형태소 단위로 분리
        tokenized_sentences = [self.okt.morphs(sentence) for sentence in sentences]
        
        # Word2Vec 모델 학습
        self.model = Word2Vec(sentences=tokenized_sentences, 
                            vector_size=100, 
                            window=5, 
                            min_count=1)
        
        # 단어 리스트 생성
        self.word_list = list(self.model.wv.index_to_key)

    def get_similarity(self, word1: str, word2: str) -> float:
        try:
            # 각 단어를 형태소로 분석
            word1_morphs = self.okt.morphs(word1)[0]
            word2_morphs = self.okt.morphs(word2)[0]
            
            # 유사도 계산
            similarity = self.model.wv.similarity(word1_morphs, word2_morphs)
            return float(similarity)
        except KeyError:
            # 단어가 모델에 없는 경우
            return 0.0
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def get_random_word(self) -> str:
        return np.random.choice(self.word_list)

    def get_rank(self, target_word: str, guess_word: str) -> int:
        try:
            target_morphs = self.okt.morphs(target_word)[0]
            similarities = []
            
            for word in self.word_list:
                try:
                    sim = self.model.wv.similarity(target_morphs, word)
                    similarities.append((word, sim))
                except:
                    continue
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            for idx, (word, _) in enumerate(similarities):
                if word == guess_word:
                    return idx + 1
            return len(similarities)
        except Exception as e:
            print(f"Error calculating rank: {e}")
            return 0