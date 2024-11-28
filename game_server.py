from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import os
from word2vec import get_random_word, calculate_similarity, is_valid_word

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 게임 상태 저장
games = {}

# index 라우트 하나로 통합
@app.route('/')
def index():
    return render_template('index.html')

# game 라우트
@app.route('/game')
def game():
    room_id = request.args.get('room_id')
    if room_id and room_id in games:
        return render_template('game.html', room=games[room_id])
    return redirect('/')

# 방 생성 API
@app.route('/api/rooms', methods=['POST'])
def create_room_api():
    try:
        data = request.get_json()
        room_id = str(len(games) + 1)
        games[room_id] = {
            'id': room_id,
            'name': data.get('name', f'Room {room_id}'),
            'players': {},
            'word': None,
            'started': False,
            'scores': {},
            'guess_history': [],
            'ready_players': set()
        }
        return jsonify({
            'status': 'success',
            'room_id': room_id
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@socketio.on('create_room')
def handle_create_room(data):
    try:
        room_id = str(len(games) + 1)
        games[room_id] = {
            'players': {},  # 플레이어 ID를 key로 사용
            'word': None,
            'started': False,
            'scores': {},
            'guess_history': [],
            'ready_players': set()
        }
        emit('room_created', {'room_id': room_id})
        print(f"Room {room_id} created")
    except Exception as e:
        print(f"Error creating room: {e}")
        return {'status': 'error', 'message': str(e)}

@socketio.on('join_room')
def handle_join_room(data):
    try:
        room_id = data.get('room_id')
        username = data.get('username')
        player_id = request.sid
        
        if not room_id or not username:
            emit('error', {'message': '방 ID와 사용자 이름이 필요합니다.'})
            return
            
        if room_id not in games:
            emit('error', {'message': '존재하지 않는 방입니다.'})
            return
        
        game = games[room_id]
        
        if player_id in game['players']:
            emit('error', {'message': '이미 참여 중인 플레이어입니다.'})
            return
        
        # 플레이어 추가
        join_room(room_id)
        game['players'][player_id] = {
            'name': username,
            'ready': False
        }
        game['scores'][username] = 0
        
        # 현재 플레이어 목록
        current_players = [p['name'] for p in game['players'].values()]
        
        # 방 정보 전송
        emit('room_joined', {
            'room_id': room_id,
            'players': current_players,
            'guess_history': game['guess_history']
        }, room=room_id)
        
        # 한 명이어도 게임 시작 가능하도록 수정
        emit('ready_to_start', {
            'message': '게임을 시작할 수 있습니다.',
            'players': current_players
        }, room=room_id)
            
    except Exception as e:
        print(f"Error in join_room: {e}")
        emit('error', {'message': f'오류가 발생했습니다: {str(e)}'})

@socketio.on('start_game')
def handle_start_game(data):
    try:
        room_id = data.get('room_id')
        if not room_id or room_id not in games:
            emit('error', {'message': '존재하지 않는 방입니다.'})
            return
        
        game = games[room_id]
    
        if game['started']:
            emit('error', {'message': '이미 게임이 시작되었습니다.'})
            return
        
        # 게임 시작
        game['word'] = get_random_word()
        game['started'] = True
        game['guess_history'] = []
        
        emit('game_started', {
            'message': '게임이 시작되었습니다!',
            'word_length': len(game['word'])
        }, room=room_id)
        
    except Exception as e:
        print(f"Error in start_game: {e}")
        emit('error', {'message': f'게임 시작 중 오류 발생: {str(e)}'})

@socketio.on('submit_guess')
def handle_guess(data):
    try:
        room_id = data.get('room_id')
        username = data.get('username')
        guess = data.get('guess', '').strip()
        
        if not room_id or room_id not in games:
            emit('error', {'message': '존재하지 않는 방입니다.'})
            return
        
        game = games[room_id]
        
        if not game['started']:
            emit('error', {'message': '게임이 시작되지 않았습니다.'})
            return
        
        if not guess:
            emit('error', {'message': '단어를 입력해주세요.'})
            return

        if not is_valid_word(guess):
            emit('error', {'message': '사전에 없는 단어입니다.'})
            return

        # 이미 시도한 단어인지 확인
        if any(record['guess'] == guess for record in game['guess_history']):
            emit('error', {'message': '이미 시도한 단어입니다.'})
            return
            
        similarity = calculate_similarity(game['word'], guess)
        
        # 추측 기록 저장
        guess_record = {
            'username': username,
            'guess': guess,
            'similarity': similarity,
            'turn': len(game['guess_history']) + 1
        }
        game['guess_history'].append(guess_record)
        
        if guess == game['word']:
            # 승리
            game['scores'][username] += 10
            print(f"Game over! Winner: {username}, Word: {game['word']}")
            emit('game_over', {
                'winner': username,
                'word': game['word'],
                'scores': game['scores'],
                'guess_history': game['guess_history']
            }, room=room_id)
            game['started'] = False
        else:
            # 게임 진행 중
            emit('guess_result', {
                'username': username,
                'guess': guess,
                'similarity': similarity,
                'scores': game['scores'],
                'guess_history': game['guess_history']
            }, room=room_id)
            
    except Exception as e:
        print(f"Error in submit_guess: {e}")
        emit('error', {'message': f'추측 처리 중 오류 발생: {str(e)}'})

@socketio.on('player_ready')
def handle_player_ready(data):
    try:
        room_id = data.get('room_id')
        player_id = request.sid
        
        if room_id not in games or player_id not in games[room_id]['players']:
            return
            
        game = games[room_id]
        game['players'][player_id]['ready'] = True
        game['ready_players'].add(player_id)
        
        # 모든 플레이어가 준비되었는지 확인
        if len(game['ready_players']) == len(game['players']):
            emit('all_players_ready', room=room_id)
            
    except Exception as e:
        print(f"Error in player_ready: {e}")

@socketio.on('leave_room')
def handle_leave_room(data):
    try:
        room_id = data.get('room_id')
        username = data.get('username')
        player_id = request.sid
        
        if room_id in games:
            game = games[room_id]
            leave_room(room_id)
            
            if player_id in game['players']:
                del game['players'][player_id]
                game['ready_players'].discard(player_id)
                
                if username in game['scores']:
                    del game['scores'][username]
                
            # 방이 비었으면 삭제
            if not game['players']:
                del games[room_id]
            else:
                # 남은 플레이어에게 알림
                current_players = [p['name'] for p in game['players'].values()]
                emit('player_left', {
                    'username': username,
                    'players': current_players
                }, room=room_id)
                
                # 게임 중이었다면 게임 종료
                if game['started']:
                    game['started'] = False
                    remaining_player = next(iter(game['players'].values()))['name']
                    emit('game_over', {
                        'winner': remaining_player,
                        'word': game['word'],
                        'reason': 'player_left'
                    }, room=room_id)
                
    except Exception as e:
        print(f"Error in leave_room: {e}")
        emit('error', {'message': f'방 나가기 중 오류 발생: {str(e)}'})

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    # 플레이어가 속한 방 찾기
    for room_id, game in list(games.items()):
        if player_id in game['players']:
            username = game['players'][player_id]['name']
            handle_leave_room({'room_id': room_id, 'username': username})
            break

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)