import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
    const [guess, setGuess] = useState('');
    const [targetWord, setTargetWord] = useState('');
    const [history, setHistory] = useState([]);
    const [message, setMessage] = useState('');

    useEffect(() => {
        startNewGame();
    }, []);

    const startNewGame = async () => {
        const response = await axios.get('/api/new-game');
        setTargetWord(response.data.target_word);
        setHistory([]);
    };

    const makeGuess = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('/api/check-similarity', {
                word: guess,
                target_word: targetWord
            });

            const newGuess = {
                word: guess,
                similarity: response.data.similarity,
                isCorrect: response.data.is_correct
            };

            setHistory([newGuess, ...history]);
            setGuess('');

            if (response.data.is_correct) {
                setMessage('정답입니다!');
            }
        } catch (error) {
            setMessage('올바르지 않은 단어입니다.');
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-4">단어 유사도 게임</h1>
            
            <form onSubmit={makeGuess} className="mb-4">
                <input
                    type="text"
                    value={guess}
                    onChange={(e) => setGuess(e.target.value)}
                    className="border p-2 mr-2"
                    placeholder="단어를 입력하세요"
                />
                <button type="submit" className="bg-blue-500 text-white p-2 rounded">
                    제출
                </button>
            </form>

            {message && (
                <div className="mb-4 text-green-600">{message}</div>
            )}

            <div className="space-y-2">
                {history.map((item, index) => (
                    <div key={index} className="border p-2">
                        <span className="font-bold">{item.word}</span>: 
                        유사도 {item.similarity.toFixed(2)}%
                    </div>
                ))}
            </div>
        </div>
    );
}

export default App;