document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const username = window.USERNAME;

    function createRoom() {
        if (!username) {
            window.location.href = '/login';
            return;
        }

        const roomName = prompt('방 이름을 입력하세요:');
        if (!roomName) return;

        fetch('/api/rooms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                name: roomName,
                username: username
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.room_id) {
                window.location.href = `/room/${data.room_id}`;
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function updateRoomsList(rooms) {
        const roomsList = document.getElementById('rooms');
        if (!rooms || rooms.length === 0) {
            roomsList.innerHTML = '<li class="no-rooms">현재 생성된 방이 없습니다.</li>';
            return;
        }

        roomsList.innerHTML = rooms.map(room => {
            const playerCount = room.players ? room.players.length : 0;
            const isLoggedIn = !!username;
            
            let joinButton;
            if (!isLoggedIn) {
                joinButton = '<span class="btn btn-secondary">참여하려면 로그인하세요</span>';
            } else if (playerCount >= 2) {
                joinButton = '<span class="room-full">방이 가득 찼습니다</span>';
            } else {
                joinButton = `<a href="/room/${room.id}" class="btn btn-primary">참여하기</a>`;
            }

            return `
                <li data-room-id="${room.id}">
                    <div class="room-info">
                        <span class="room-name">${room.name}</span>
                        <span class="player-count">참가자 ${playerCount}/2</span>
                    </div>
                    ${joinButton}
                </li>
            `;
        }).join('');
    }

    // 방 삭제 이벤트 리스너
    socket.on('room_closed', data => {
        const roomElement = document.querySelector(`li[data-room-id="${data.room_id}"]`);
        if (roomElement) {
            roomElement.remove();
            
            const roomsList = document.getElementById('rooms');
            if (!roomsList.children.length) {
                roomsList.innerHTML = '<li class="no-rooms">현재 생성된 방이 없습니다.</li>';
            }
        }
    });

    // 방 목록 업데이트 이벤트 리스너
    socket.on('rooms_update', updateRoomsList);

    // 초기 방 목록 로드
    fetch('/api/rooms')
        .then(response => response.json())
        .then(rooms => updateRoomsList(rooms))
        .catch(error => console.error('Error:', error));

    // createRoom 함수를 전역으로 노출
    window.createRoom = createRoom;
}); 