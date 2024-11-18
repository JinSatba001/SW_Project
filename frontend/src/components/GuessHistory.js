import React from 'react';

const GuessHistory = ({ history }) => (
    <div className="space-y-2">
        {history.map((guess, index) => (
            <div key={index} className="border p-2 rounded">
                <span className="font-bold">{guess.word}</span>
                <div>유사도: {guess.similarity.toFixed(2)}%</div>
                {guess.rank && <div>순위: {guess.rank}위</div>}
            </div>
        ))}
    </div>
);

export default GuessHistory;