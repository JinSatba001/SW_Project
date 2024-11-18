import React, { useState, useEffect } from 'react';
import GuessForm from './GuessForm';
import GuessHistory from './GuessHistory';
import axios from 'axios';

const Game = () => {
    const [targetWord, setTargetWord] = useState('');
    const [history, setHistory] = useState([]);
    const [gameWon, setGameWon] = useState(false);

    useEffect(() => {
        startNewGame();
    }, []);

    const startNewGame = async () => {
        const response = await axios.get('/api/new-game');
        setTargetWord(response.data.target_word);
        setHistory([]);
        setGameWon(false);
    };

    const makeGuess = async (word) => {
        try {
            const response = await axios.post('/api/check-similarity', {
                word,
                target_word: targetWord
            });

            const newGuess = {
                word,
                similarity: response.data.similarity,
                rank: response.data.rank,
                isCorrect: response.data.is_correct
            };

            setHistory([newGuess, ...history]);
            
            if (response.data.is_correct) {
                setGameWon(true);
            }

            return newGuess;
        } catch (error) {
            throw new Error('올바르지 않은 단어입니다.');
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-4">단어 유사도 게임</h1>
            
            <GuessForm onGuess={makeGuess} disabled={gameWon} />
            
            {gameWon && (
                <div className="my-4">
                    <h2 className="text-2xl text-green-600">축하합니다! 정답을 맞추셨습니다!</h2>
                    <button
                        onClick={startNewGame}
                        className="mt-2 bg-blue-500 text-white px-4 py-2 rounded"
                    >
                        새 게임 시작
                    </button>
                </div>
            )}
            
            <GuessHistory history={history} />
        </div>
    );
};

export default Game;