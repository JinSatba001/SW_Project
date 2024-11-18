import pytest
from app.services.word_similarity import WordSimilarityService

def test_similarity_calculation():
    service = WordSimilarityService()
    similarity = service.get_similarity("강아지", "고양이")
    assert 0 <= similarity <= 1

def test_invalid_word():
    service = WordSimilarityService()
    with pytest.raises(ValueError):
        service.get_similarity("존재하지않는단어", "강아지")