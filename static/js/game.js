document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const roomId = window.ROOM_ID;
    const username = window.USERNAME;
    let gameStarted = false;
    let currentTurn = null;
    let guessed = new Set();

    if (!username) {
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        return;
    }

    // 이벤트 리스너 설정
    setupEventListeners();
    
    // 소켓 이벤트 리스너 설정
    setupSocketListeners();
    
    // 방 참가
    joinRoom();

    function setupEventListeners() {
        // 나가기 버튼 클릭 이벤트
        document.getElementById('leave-button').addEventListener('click', leaveGame);

        // 페이지 나갈 때 자동 방 나가기
        window.addEventListener('beforeunload', () => {
            socket.emit('leave_game', {
                room_id: roomId,
                username: username
            });
        });

        // 게임 시작 버튼
        document.getElementById('start-button').onclick = () => {
            socket.emit('start_game', { room_id: roomId });
        };

        // 추측 제출 폼
        document.getElementById('guess-form').addEventListener('submit', handleGuessSubmit);
    }

    function setupSocketListeners() {
        socket.on('room_joined', handleRoomJoined);
        socket.on('guess_result', handleGuessResult);
        socket.on('game_over', handleGameOver);
        socket.on('player_left', data => updatePlayerList(data.players));
        socket.on('error', handleError);
        socket.on('show_answer', handleShowAnswer);
        socket.on('game_started', handleGameStarted);
        socket.on('game_reset', handleGameReset);
        socket.on('room_closed', handleRoomClosed);
    }

    // 여기에 나머지 함수들 구현...
    // updatePlayerList, updateGuessLog, handleGuessSubmit 등
    // 기존 JavaScript 코드의 나머지 함수들을 여기에 옮깁니다.
}); 