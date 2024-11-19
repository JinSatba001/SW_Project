const socket = io();
let currentRoom = null;
let username = null;

function setUsername() {
    const usernameInput = document.getElementById('username');
    const name = usernameInput.value.trim();
    
    if (name) {
        username = name;
        document.getElementById('room-controls').style.display = 'block';
        usernameInput.disabled = true;
    } else {
        alert('닉네임을 입력해주세요!');
    }
}

function createRoom() {
    if (!username) {
        alert('먼저 닉네임을 설정해주세요!');
        return;
    }
    
    socket.emit('create_room', { username: username });
}

function joinRoom() {
    if (!username) {
        alert('먼저 닉네임을 설정해주세요!');
        return;
    }
    
    const roomId = document.getElementById('room-id-input').value.trim();
    if (roomId) {
        socket.emit('join_room', {
            room_id: roomId,
            username: username
        });
    } else {
        alert('방 번호를 입력해주세요!');
    }
}

function startGame() {
    if (!currentRoom) {
        alert('방에 입장해 있지 않습니다.');
        return;
    }
    
    socket.emit('start_game', {
        room_id: currentRoom
    });
}

function submitGuess() {
    const input = document.getElementById('guess-input');
    const guess = input.value.trim();
    
    if (guess && currentRoom) {
        socket.emit('submit_guess', {
            room_id: currentRoom,
            username: username,
            guess: guess
        });
        input.value = '';
    }
}

function leaveRoom() {
    if (currentRoom) {
        socket.emit('leave_room', {
            room_id: currentRoom,
            username: username
        });
        
        currentRoom = null;
        document.getElementById('lobby').style.display = 'block';
        document.getElementById('game-room').style.display = 'none';
        document.getElementById('current-room').textContent = '';
        document.getElementById('players-list').innerHTML = '';
        document.getElementById('guess-results').innerHTML = '';
    }
}

// Socket event listeners
socket.on('room_created', (data) => {
    currentRoom = data.room_id;
    showGameRoom();
});

socket.on('room_joined', (data) => {
    currentRoom = data.room_id;
    showGameRoom();
    updatePlayersList(data.players);
});

socket.on('ready_to_start', () => {
    document.getElementById('start-section').style.display = 'block';
});

socket.on('game_started', (data) => {
    document.getElementById('start-section').style.display = 'none';
    document.getElementById('game-section').style.display = 'block';
    addGameMessage(data.message + '\n단어는 ' + data.word_length + '글자입니다.');
});

socket.on('guess_result', (data) => {
    const similarity = (data.similarity * 100).toFixed(2);
    addGameMessage(`${data.username}의 추측: ${data.guess} (유사도: ${similarity}%)`);
});

socket.on('game_over', (data) => {
    addGameMessage(`🎉 승자: ${data.winner}\n정답: ${data.word}`, true);
    document.getElementById('game-section').style.display = 'none';
});

socket.on('player_left', (data) => {
    addGameMessage(`${data.username}님이 퇴장하셨습니다.`);
});

socket.on('error', (data) => {
    alert(data.message);
});

// Helper functions
function showGameRoom() {
    document.getElementById('lobby').style.display = 'none';
    document.getElementById('game-room').style.display = 'block';
    document.getElementById('current-room').textContent = currentRoom;
}

function updatePlayersList(players) {
    const playersList = document.getElementById('players-list');
    playersList.innerHTML = players.map(player => 
        `<div class="player-card">${player}</div>`
    ).join('');
}

function addGameMessage(message, isWinner = false) {
    const results = document.getElementById('guess-results');
    const div = document.createElement('div');
    div.className = `guess-result${isWinner ? ' winner' : ''}`;
    div.textContent = message;
    results
}