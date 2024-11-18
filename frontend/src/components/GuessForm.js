import React, { useState } from 'react';

const GuessForm = ({ onGuess, disabled }) => {
    const [guess, setGuess] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        
        try {
            await onGuess(guess);
            setGuess('');
        } catch (error) {
            setError(error.message);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="mb-4">
            <input
                type="text"
                value={guess}
                onChange={(e) => setGuess(e.target.value)}
                disabled={disabled}
                className="border p-2 mr-2"
                placeholder="단어를 입력하세요"
            />
            <button
                type="submit"
                disabled={disabled}
                className="bg-blue-500 text-white p-2 rounded disabled:bg-gray-400"
            >
                제출
            </button>
            {error && <div className="text-red-500 mt-2">{error}</div>}
        </form>
    );
};

export default GuessForm;