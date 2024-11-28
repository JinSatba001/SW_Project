// Socket.IO 초기화 및 연결 관리
const socket = io({
    path: '/socket.io',
    transports: ['websocket', 'polling'],
    upgrade: true,
    rememberUpgrade: true,
    timeout: 60000,
    reconnection: true,
    reconnectionAttempts: 5
});

// 게임 상태 관리
let currentGame = null;

// 연결 이벤트 핸들러
socket.on('connect', () => {
    console.log('Connected to server');
    
    // 사용자 이름이 있다면 서버에 전송
    const username = localStorage.getItem('username');
    if (username) {
        socket.emit('join_game', { username });
    }
});

// 게임 상태 업데이트 수신
socket.on('game_state', (gameState) => {
    currentGame = gameState;
    updateGameUI(gameState);
});

// 오류 처리
socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
});

socket.on('error', (error) => {
    console.error('Socket error:', error);
});

// 연결 해제
socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
});

// UI 업데이트 함수
function updateGameUI(gameState) {
    const playerList = gameState.players;
    
    // player1 상태 업데이트
    const player1Element = document.getElementById('player1');
    if (player1Element) {
        player1Element.textContent = playerList.player1?.name || '대기 중';
    }
    
    // player2 상태 업데이트
    const player2Element = document.getElementById('player2');
    if (player2Element) {
        player2Element.textContent = playerList.player2?.name || '대기 중';
    }
}

// 게임 참가 함수
function joinGame(username) {
    if (!socket.connected) {
        console.error('Socket not connected');
        return;
    }
    
    socket.emit('join_game', { username });
    localStorage.setItem('username', username);
}

// 게임 나가기 함수
function leaveGame() {
    if (!socket.connected) {
        console.error('Socket not connected');
        return;
    }
    
    socket.emit('leave_game');
    localStorage.removeItem('username');
} 