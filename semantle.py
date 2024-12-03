from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from redis import Redis
from flask_session import Session
import pickle
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta, datetime
from dataclasses import dataclass
from typing import Optional, List
import json
import random
import uuid
from functools import wraps
from word2vec import calculate_similarity, get_random_word

# Flask 앱 초기화
app = Flask(__name__)

# Redis 연결 설정 - Flask-Session용
session_redis = Redis(
    host='redis',
    port=6379,
    db=0,
    decode_responses=False  # Flask-Session은 바이너리 데이터를 사용
)

# Redis 연결 설정 - 애플리케이션 데이터용
redis_client = Redis(
    host='redis',
    port=6379,
    db=1,  # 다른 DB 사용
    decode_responses=True,  # 일반 데이터는 문자열로 디코딩
    charset="utf-8"
)

# Flask 앱 설정
app.config.update(
    SESSION_TYPE='redis',
    SESSION_REDIS=session_redis,
    SESSION_KEY_PREFIX='semantle_session:',
    PERMANENT_SESSION_LIFETIME=timedelta(days=31),
    SECRET_KEY=os.urandom(24),
    SESSION_USE_SIGNER=True
)

# Session 초기화
Session(app)

# 게임방 관리를 위한 전역 변수
rooms = {}

@dataclass
class User:
    username: str
    password_hash: str
    current_word: Optional[str] = None
    guess_history: list = None
    
    def __post_init__(self):
        if self.guess_history is None:
            self.guess_history = []

# Redis 연결 테스트 함수
def test_redis_connection():
    try:
        redis_client.ping()
        print("Redis connection successful")
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

# 사용자 데이터 처리 함수들
def serialize_user(user_data):
    """사용자 데이터를 JSON으로 직렬화"""
    return json.dumps(user_data)

def deserialize_user(user_data):
    """JSON 문자열을 사용자 데이터로 역직렬화"""
    try:
        return json.loads(user_data) if user_data else None
    except:
        return None

# 사용자 관리 함수들
def get_user(username):
    try:
        user_data = redis_client.get(f"user:{username}")
        return json.loads(user_data) if user_data else None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def create_user(username, password):
    try:
        if redis_client.exists(f"user:{username}"):
            return False, "이미 존재하는 사용자입니다"
        
        user_data = {
            "username": username,
            "password": generate_password_hash(password),
            "created_at": datetime.now().isoformat()
        }
        
        redis_client.set(
            f"user:{username}",
            json.dumps(user_data)
        )
        return True, "회원가입이 완료되었습니다"
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, "회원가입 처리 중 오류가 발생했습니다"

# 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 게임 관련 함수들
def get_random_word():
    words = load_words()
    return random.choice(words)

def load_words():
    try:
        with open('words.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading words: {e}")
        return []

def calculate_similarity(word1, word2):
    # 실제 유사도 계산 로직 구현 필요
    return random.random()

# 라우트들
@app.route('/')
def index():
    return render_template('index.html', 
        rooms=rooms,
        logged_in='user_id' in session,
        username=session.get('user_id'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:  # 이미 로그인된 경우
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username
            session.permanent = True  # 세션 유지
            
            # next 파라미터가 있으면 해당 페이지로, 없으면 메인으로
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  # 보안을 위한 체크
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('잘못된 사용자명 또는 비밀번호입니다')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, message = create_user(username, password)
        if success:
            return redirect(url_for('login'))
        
        flash(message)
    return render_template('register.html')

@app.route('/game')
@login_required
def game():
    username = session.get('user_id')
    room_id = request.args.get('room')
    
    if not username:
        return redirect(url_for('login', next=request.path))
    
    if room_id and room_id in rooms:
        return render_template('game.html',
            room=rooms[room_id],
            room_id=room_id,
            username=username)
    
    return render_template('game.html',
        available_rooms=rooms,
        username=username)

@app.route('/test-redis')
def test_redis():
    if test_redis_connection():
        return jsonify({"status": "success", "message": "Redis connection successful"})
    return jsonify({"status": "error", "message": "Redis connection failed"}), 500

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('로그아웃되었습니다')
    return redirect(url_for('index'))

@app.route('/room/<room_id>')
@login_required
def room(room_id):
    if room_id not in rooms:
        flash('존재하지 않는 방입니다.')
        return redirect(url_for('index'))
        
    return render_template('game.html',
                         room_id=room_id,
                         room_name=rooms[room_id]['name'],  # 방 이름 전달
                         username=session.get('user_id'))

@app.route('/api/rooms', methods=['POST'])
@login_required
def create_room():
    username = session.get('user_id')
    data = request.get_json()
    room_id = str(uuid.uuid4())
    room_name = data.get('name', f"{username}의 방")
    
    rooms[room_id] = {
        'id': room_id,
        'name': room_name,  # 방 이름 저장
        'players': [username],
        'word': None,
        'created_at': datetime.now().isoformat(),
        'status': 'waiting',
        'started': False,
        'guess_history': [],
        'scores': {}
    }
    
    broadcast_rooms_update()  # 방 생성 시 목록 업데이트
    return jsonify({'room_id': room_id})

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    rooms_data = [{
        'id': room_id,
        'name': room['name'],
        'players': room['players']
    } for room_id, room in rooms.items()]
    return jsonify(rooms_data)

def broadcast_rooms_update():
    """방 목록 업데이트를 모든 클라이언트에게 전송"""
    try:
        rooms_data = [{
            'id': room_id,
            'name': room['name'],
            'players': room['players'],
            'status': room.get('status', 'waiting')
        } for room_id, room in rooms.items()]
        
        socketio.emit('rooms_update', rooms_data)
    except Exception as e:
        print(f"Error in broadcast_rooms_update: {e}")

# Socket.IO 초기화
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    message_queue='redis://redis:6379/0',
    manage_session=False
)

# Socket.IO 이벤트 핸들러들
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    return True

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join(data):
    username = session.get('user_id')
    if not username:
        return False
    
    room_id = data.get('room_id')
    if not room_id or room_id not in rooms:
        emit('error', {'message': '잘못된 방 정보입니다.'})
        return False
    
    game = rooms[room_id]
    
    # 플레이어가 아직 방에 없다면 추가
    if username not in game['players']:
        game['players'].append(username)
    
    join_room(room_id)
    
    # 방 정보 전송
    emit('room_joined', {
        'room_id': room_id,
        'name': game['name'],
        'players': game['players'],
        'started': game.get('started', False),
        'guess_history': game.get('guess_history', [])
    }, room=room_id)
    
    broadcast_rooms_update()
    return True

@socketio.on('leave_game')
def handle_leave(data):
    try:
        username = data.get('username') or session.get('user_id')
        room_id = data.get('room_id')
        
        if not room_id or room_id not in rooms:
            return
            
        game = rooms[room_id]
        if username in game['players']:
            # 플레이어 제거
            game['players'].remove(username)
            leave_room(room_id)
            
            # 방에 아무도 없으면 방 삭제
            if not game['players']:
                del rooms[room_id]
                socketio.emit('room_closed', {'room_id': room_id})
            else:
                # 방장이 나간 경우 다음 사람에게 방장 권한 이전
                new_host = game['players'][0] if game['players'] else None
                emit('player_left', {
                    'username': username,
                    'players': game['players'],
                    'is_host': new_host
                }, room=room_id)
                
                # 게임 중이었다면 게임 초기화
                if game.get('started', False):
                    game.update({
                        'started': False,
                        'word': None,
                        'guess_history': [],
                        'scores': {}
                    })
                    emit('game_reset', {
                        'message': '플레이어가 나가서 게임이 초기화되었습니다.'
                    }, room=room_id)
            
            # 방 목록 업데이트를 모든 클라이언트에게 브로드캐스트
            broadcast_rooms_update()
            
            return {'success': True}
            
    except Exception as e:
        print(f"Error in leave_game: {e}")
        return {'success': False, 'error': str(e)}

@socketio.on('submit_guess')
def handle_guess(data):
    try:
        room_id = data.get('room_id')
        username = data.get('username')
        guess = data.get('guess', '').strip()
        
        if not all([room_id, username, guess]) or room_id not in rooms:
            emit('error', {'message': '잘못된 요청입니다.'})
            return
        
        game = rooms[room_id]
        
        if not game['started']:
            emit('error', {'message': '게임이 시작되지 않았습니다.'})
            return
        
        # 턴 체크
        current_turn = len(game['guess_history']) % len(game['players'])
        current_player = game['players'][current_turn]
        
        if username != current_player:
            emit('error', {'message': f'{current_player}님의 차례입니다.'})
            return
            
        # 비밀 명령어 처리
        if guess in ['/정답', '!정답']:
            emit('show_answer', {
                'word': game['word'],
                'message': f'정답은 "{game["word"]}" 입니다.'
            }, room=room_id)
            return
            
        # 이미 시도한 단어인지 확인
        if any(record['guess'] == guess for record in game['guess_history']):
            emit('error', {'message': '이미 시도한 단어입니다.'})
            return
            
        # word2vec의 유사도 계산 함수 사용
        target_word = game['word']
        similarity = calculate_similarity(target_word, guess)  # word2vec의 함수 사용
        
        # 추측 기록 저장
        guess_record = {
            'username': username,
            'guess': guess,
            'similarity': similarity,
            'timestamp': datetime.now().isoformat(),
            'turn': len(game['guess_history']) + 1
        }
        game['guess_history'].append(guess_record)
        
        # 정답 여부 확인
        if guess == target_word:
            # 승리 점수 부여
            game['scores'][username] = game['scores'].get(username, 0) + 10
            emit('game_over', {
                'winner': username,
                'word': target_word,
                'scores': game['scores'],
                'guess_history': game['guess_history']
            }, room=room_id)
            
            # 게임 초기화
            game.update({
                'started': False,
                'word': None,
                'guess_history': [],
                'scores': {}
            })
            
            # 게임 종료 후 상태 업데이트
            emit('game_reset', {
                'message': '게임이 종료되었습니다. 새 게임을 시작할 수 있습니다.'
            }, room=room_id)
            
        else:
            # 게임 진행 중일 때 다음 플레이어 턴 알림 추가
            next_turn = (current_turn + 1) % len(game['players'])
            next_player = game['players'][next_turn]
            
            emit('guess_result', {
                'username': username,
                'guess': guess,
                'similarity': similarity,
                'scores': game['scores'],
                'guess_history': game['guess_history'],
                'next_player': next_player  # 다음 플레이어 정보 추가
            }, room=room_id)
            
    except Exception as e:
        print(f"Error in submit_guess: {e}")
        emit('error', {'message': f'추측 처리 중 오류 발생: {str(e)}'})

@socketio.on('start_game')
def handle_start_game(data):
    try:
        room_id = data.get('room_id')
        username = session.get('user_id')
        
        if not room_id or room_id not in rooms:
            emit('error', {'message': '잘못된 방 정보입니다.'})
            return
            
        game = rooms[room_id]
        
        if game['started']:
            emit('error', {'message': '이미 게임이 시작되었습니다.'})
            return
            
        # 2명이 아니면 게임 시작 불가
        if len(game['players']) != 2:
            emit('error', {'message': '게임을 시작하려면 2명의 플레이어가 필요합니다.'})
            return
            
        # 게임 시작 처리
        game['started'] = True
        game['word'] = get_random_word()
        game['guess_history'] = []
        game['scores'] = {}
        
        # 첫 번째 플레이어 턴 설정
        first_player = game['players'][0]
        
        # 모든 참가자에게 게임 시작 알림
        emit('game_started', {
            'message': '게임이 시작되었습니다!',
            'word_length': len(game['word']),
            'first_player': first_player  # 첫 번째 플레이어 정보 추가
        }, room=room_id)
        
    except Exception as e:
        print(f"Error in start_game: {e}")
        emit('error', {'message': f'게임 시작 중 오류 발생: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')