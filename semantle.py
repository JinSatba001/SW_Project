import pickle
import random
from datetime import date, datetime
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import (
    Flask,
    send_file,
    send_from_directory,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from pytz import utc, timezone
from flask_socketio import SocketIO, emit, join_room, leave_room
from redis import Redis

import hashlib
import word2vec
from process_similar import get_nearest


app = Flask(__name__)
app.secret_key = 'your-secret-key'
redis_client = Redis(host='redis', port=6379, db=0)
socketio = SocketIO(app)

rooms = {}

print("loading valid nearest")
with open('data/valid_nearest.dat', 'rb') as f:
    valid_nearest_words, valid_nearest_vecs = pickle.load(f)
with open('data/secrets.txt', 'r', encoding='utf-8') as f:
    secrets = [l.strip() for l in f.readlines()]
print("initializing nearest words for solutions")
app.secrets = dict()
app.nearests = dict()

# 고정된 puzzle_number 사용
puzzle_number = 0  # 또는 원하는 시작 번호

for offset in range(-2, 2):
    current_puzzle = puzzle_number + offset
    secret_word = secrets[current_puzzle % len(secrets)]  # secrets 배열의 범위를 벗어나지 않도록 수정
    app.secrets[current_puzzle] = secret_word
    app.nearests[current_puzzle] = get_nearest(current_puzzle, secret_word, valid_nearest_words, valid_nearest_vecs)



@app.route('/robots.txt')
def robots():
    return send_file("static/assets/robots.txt")


@app.route("/favicon.ico")
def send_favicon():
    return send_file("static/assets/favicon.ico")


@app.route("/assets/<path:path>")
def send_static(path):
    return send_from_directory("static/assets", path)


@app.route('/similarity/<int:day>')
def get_similarity(day: int):
    nearest_dists = sorted([v[1] for v in app.nearests[day].values()])
    return jsonify({"top": nearest_dists[-2], "top10": nearest_dists[-11], "rest": nearest_dists[0]})

# 로그인 상태 확인 데코레이터 추가
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def get_index():
    return render_template('index.html', rooms=rooms, username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('get_index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        stored_password = redis_client.hget('users', username)
        
        if stored_password and stored_password.decode() == hashed_password:
            session['username'] = username
            return redirect(url_for('get_index'))
        return '로그인 실패'
    
    return render_template('login.html')

@app.route('/create-room', methods=['POST'])
@login_required
def create_room():
    room_id = str(len(rooms) + 1)
    secret_word = random.choice(secrets)
    nearest_data = get_nearest(0, secret_word, valid_nearest_words, valid_nearest_vecs)  # puzzle_number 대신 0 사용
    rooms[room_id] = {
        "name": f"게임방 {room_id}", 
        "secret": secret_word,
        "nearest": nearest_data,
        "players": []  
    }
    return jsonify({"room_id": room_id})


@app.route('/room/<string:room_id>')
def room_detail(room_id):
    """특정 방의 상세 정보"""
    if room_id not in rooms:
        return "Room not found", 404
    room_data = rooms[room_id]
    return render_template('room.html', room_id=room_id, secret=room_data["secret"])


@app.route('/guess/<string:room_id>/<string:word>')
def get_room_guess(room_id, word):
    """단어 추측"""
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404

    secret_word = rooms[room_id]["secret"]
    nearest_data = rooms[room_id]["nearest"]

    if word == secret_word:
        return jsonify({"guess": word, "sim": 1.0, "rank": "정답!"})

    rtn = {"guess": word}
    if word in nearest_data:
        rtn["sim"] = nearest_data[word][1]
        rtn["rank"] = nearest_data[word][0]
    else:
        try:
            rtn["sim"] = similarity(secret_word, word)
            rtn["rank"] = "1000위 이상"
        except KeyError:
            return jsonify({"error": "unknown"}), 404

    return jsonify(rtn)


@app.route('/giveup/<int:day>')
def give_up(day: int):
    if day not in app.secrets:
        return '저런...', 404
    else:
        return app.secrets[day]


@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """방 목록 조회"""
    room_list = [{'id': k, 'name': v['name'], 'players': len(v['players'])} for k, v in rooms.items()]
    return jsonify(room_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if redis_client.hexists('users', username):
            return '이미 존재하는 사용자입니다.'
        
        redis_client.hset('users', username, hashed_password)
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('join')
def on_join(data):
    """방 참여"""
    room_id = data['room_id']
    if room_id in rooms:
        join_room(room_id)
        rooms[room_id]['players'].append(request.sid)
        emit('user_joined', {'room_id': room_id}, room=room_id)


@socketio.on('leave')
def on_leave(data):
    """방 나가기"""
    room_id = data['room_id']
    if room_id in rooms:
        leave_room(room_id)
        rooms[room_id]['players'].remove(request.sid)
        emit('user_left', {'room_id': room_id}, room=room_id)

def similarity(word1, word2):
    """두 단어 간의 유사도를 계산하는 함수"""
    try:
        return word2vec.similarity(word1, word2)
    except KeyError:
        return 0.0


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
