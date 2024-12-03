from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import os
import word2vec

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 게임 상태 저장
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def handle_create_room(data):
    try:
        room_id = str(len(games) + 1)
        games[room_id] = {
            'players': [],
            'word': None,
            'started': False,
            'scores': {}
        }
        emit('room_created', {'room_id': room_id})
        return {'status': 'success', 'room_id': room_id}
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
        
        current_players = [p['name'] for p in game['players'].values()]
        
        emit('room_joined', {
            'room_id': room_id,
            'players': current_players,
            'guess_history': game.get('guess_history', [])
        }, room=room_id)
        
        # 플레이어가 2명 이상이면 게임 시작 가능 알림
        if len(game['players']) >= 2:
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
        
        if len(game['players']) < 2:
            emit('error', {'message': '플레이어가 부족합니다.'})
            return
        
        # 게임 시작
        game['word'] = word2vec.get_random_word()
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
    room_id = data['room_id']
    username = data['username']
    guess = data['guess']
    
    if room_id not in games:
        emit('error', {'message': '존재하지 않는 방입니다.'})
        return
    
    game = games[room_id]
    if not game['started']:
        emit('error', {'message': '게임이 시작되지 않았습니다.'})
        return
    
    similarity = word2vec.calculate_similarity(game['word'], guess)
    
    if guess == game['word']:
        game['scores'][username] += 10
        emit('game_over', {
            'winner': username,
            'word': game['word'],
            'scores': game['scores']
        }, room=room_id)
        game['started'] = False
    else:
        emit('guess_result', {
            'username': username,
            'guess': guess,
            'similarity': similarity,
            'scores': game['scores']
        }, room=room_id)

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data['room_id']
    username = data['username']
    
    if room_id in games:
        leave_room(room_id)
        if username in games[room_id]['players']:
            games[room_id]['players'].remove(username)
        
        if not games[room_id]['players']:
            del games[room_id]
        else:
            emit('player_left', {'username': username}, room=room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8899, debug=True)