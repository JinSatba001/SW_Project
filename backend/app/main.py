from fastapi import FastAPI, HTTPException
from .models import GuessRequest, GuessResponse
from .services.word_similarity import WordSimilarityService

app = FastAPI()
word_service = WordSimilarityService()

@app.post("/api/check-similarity", response_model=GuessResponse)
async def check_similarity(guess: GuessRequest):
    try:
        similarity = word_service.get_similarity(guess.word, guess.target_word)
        rank = word_service.get_rank(guess.target_word, guess.word)
        return GuessResponse(
            similarity=float(similarity * 100),
            is_correct=guess.word == guess.target_word,
            rank=rank
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/new-game")
async def new_game():
    target_word = word_service.get_random_word()
    return {"target_word": target_word}