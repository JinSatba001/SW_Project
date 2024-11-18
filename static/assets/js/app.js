const socket = io();

function joinGame() {
    const username = document.getElementById('username').value;
    const room = document.getElementById('room').value;

    socket.emit('join_game', { username, room });
    document.getElementById('lobby').style.display = 'none';
    document.getElementById('game').style.display = 'block';
    document.getElementById('room-name').innerText = room;
}

function submitGuess() {
    const guess = document.getElementById('guess').value;
    const room = document.getElementById('room-name').innerText;
    const username = document.getElementById('username').value;

    socket.emit('submit_guess', { room, username, guess });
}

function leaveGame() {
    const room = document.getElementById('room-name').innerText;
    const username = document.getElementById('username').value;

    socket.emit('leave_game', { room, username });
    document.getElementById('game').style.display = 'none';
    document.getElementById('lobby').style.display = 'block';
}

socket.on('player_joined', (data) => {
    document.getElementById('players').innerText = 'Players: ' + data.players.join(', ');
});

socket.on('start_game', (data) => {
    alert(data.message);
});

socket.on('guess_result', (data) => {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML += `<p>Guess: ${data.word}, Result: ${data.result}, Hint: ${data.hint}</p>`;
});

socket.on('player_left', (data) => {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML += `<p>${data.username} has left the room.</p>`;
});
