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
        return redirect(url_for('game'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username
            session.permanent = True  # 세션 유지
            return redirect(url_for('game'))
        
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
    username = session.get('user_id')
    
    if room_id not in rooms:
        flash('존재하지 않는 방입니다')
        return redirect(url_for('index'))
        
    return render_template('game.html',
        room=rooms[room_id],
        room_id=room_id,
        username=username)

@app.route('/api/rooms', methods=['POST'])
@login_required
def create_room():
    username = session.get('user_id')
    data = request.get_json()
    room_id = str(uuid.uuid4())
    
    rooms[room_id] = {
        'id': room_id,
        'name': data.get('name', f"{username}의 방"),
        'players': [username],
        'word': get_random_word(),
        'created_at': datetime.now().isoformat(),
        'status': 'waiting'
    }
    
    return jsonify({'room_id': room_id})

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

@socketio.on('join_game')
def handle_join(data):
    username = session.get('user_id')
    if not username:
        return False
    
    room_id = data.get('room_id', str(uuid.uuid4()))
    
    # 새로운 방 생성 또는 기존 방 참가
    if room_id not in rooms:
        rooms[room_id] = {
            'players': [],
            'word': get_random_word(),
            'created_at': datetime.now().isoformat(),
            'status': 'waiting'  # waiting, playing, finished
        }
    
    # 플레이어가 아직 방에 없다면 추가
    if username not in rooms[room_id]['players']:
        rooms[room_id]['players'].append(username)
    
    join_room(room_id)
    
    emit('room_joined', {
        'room_id': room_id,
        'username': username,
        'players': rooms[room_id]['players'],
        'status': rooms[room_id]['status']
    }, room=room_id)
    
    broadcast_rooms_update()  # 방 목록 업데이트 브로드캐스트
    return True

@socketio.on('leave_game')
def handle_leave(data):
    username = session.get('user_id')
    room_id = data.get('room_id')
    
    if room_id in rooms and username in rooms[room_id]['players']:
        rooms[room_id]['players'].remove(username)
        leave_room(room_id)
        
        if not rooms[room_id]['players']:
            del rooms[room_id]
            socketio.emit('room_closed', {'room_id': room_id})
        else:
            emit('player_left', {
                'username': username,
                'players': rooms[room_id]['players']
            }, room=room_id)
        
        broadcast_rooms_update()  # 방 목록 업데이트 브로드캐스트

@socketio.on('make_guess')
def handle_guess(data):
    username = session.get('user_id')
    room_id = data.get('room_id')
    guess = data.get('guess')
    
    if not all([username, room_id, guess]) or room_id not in rooms:
        return False
    
    result = {
        'username': username,
        'guess': guess,
        'correct': guess == rooms[room_id]['word'],
        'similarity': calculate_similarity(guess, rooms[room_id]['word'])
    }
    
    emit('guess_result', result, room=room_id)
    return True

def broadcast_rooms_update():
    rooms_data = [{
        'id': room_id,
        'name': room['name'],
        'players': room['players']
    } for room_id, room in rooms.items()]
    
    socketio.emit('rooms_update', rooms_data)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')