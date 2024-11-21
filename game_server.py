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
    room_id = data['room_id']
    username = data['username']
    
    if room_id not in games:
        emit('error', {'message': '존재하지 않는 방입니다.'})
        return
    
    if len(games[room_id]['players']) >= 2:
        emit('error', {'message': '방이 가득 찼습니다.'})
        return
    
    join_room(room_id)
    games[room_id]['players'].append(username)
    games[room_id]['scores'][username] = 0
    
    emit('room_joined', {
        'room_id': room_id,
        'players': games[room_id]['players']
    }, room=room_id)
    
    if len(games[room_id]['players']) == 2:
        emit('ready_to_start', room=room_id)

@socketio.on('start_game')
def handle_start_game(data):
    room_id = data['room_id']
    if room_id not in games:
        emit('error', {'message': '존재하지 않는 방입니다.'})
        return
    
    game = games[room_id]
    if len(game['players']) < 2:
        emit('error', {'message': '플레이어가 부족합니다.'})
        return
    
    game['word'] = word2vec.get_random_word()
    game['started'] = True
    
    emit('game_started', {
        'message': '게임이 시작되었습니다!',
        'word_length': len(game['word'])
    }, room=room_id)

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