import os
import pickle
import random
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room

# Flask와 SocketIO 초기화
app = Flask(__name__)
socketio = SocketIO(app)

# 게임 세션 저장소
games = {}  # {room_id: {'players': [], 'secret_word': str, 'scores': {player1: int, player2: int}}}

# 데이터 파일 경로
data_dir = 'data'
secrets_file = os.path.join(data_dir, 'secrets.txt')
valid_nearest_file = os.path.join(data_dir, 'valid_nearest.dat')

# 정답 단어 리스트 로드
if not os.path.exists(secrets_file):
    raise FileNotFoundError(f"{secrets_file} 파일이 없습니다. 단어 리스트를 추가하세요.")
with open(secrets_file, 'r', encoding='utf-8') as f:
    secret_words = [line.strip() for line in f.readlines()]

# 단어 유사도 데이터 로드
if os.path.exists(valid_nearest_file):
    print(f"Loading data from {valid_nearest_file}...")
    with open(valid_nearest_file, 'rb') as f:
        valid_nearest_words, valid_nearest_vecs = pickle.load(f)
else:
    print(f"{valid_nearest_file} not found. Creating default data...")
    os.makedirs(data_dir, exist_ok=True)
    valid_nearest_words, valid_nearest_vecs = {}, {}
    with open(valid_nearest_file, 'wb') as f:
        pickle.dump((valid_nearest_words, valid_nearest_vecs), f)
    print(f"{valid_nearest_file} created successfully with default values.")


def calculate_similarity(secret_word, guess_word):
    """단어 유사도 계산"""
    if secret_word == guess_word:
        return 1.0  # 동일 단어일 경우 최대 유사도 반환
    return random.uniform(0, 1)  # 예제에서는 랜덤 유사도 반환 (실제 유사도 계산 로직을 추가하세요)


@app.route('/')
def index():
    """메인 페이지 반환"""
    return render_template('index.html')



@socketio.on('join_game')
def handle_join_game(data):
    """플레이어가 게임 방에 참여"""
    room = data['room']
    username = data['username']
    join_room(room)

    if room not in games:
        games[room] = {'players': [], 'secret_word': random.choice(secret_words), 'scores': {}}

    games[room]['players'].append(username)
    games[room]['scores'][username] = 0

    emit('player_joined', {'players': games[room]['players']}, to=room)

    if len(games[room]['players']) == 2:
        emit('start_game', {
            'message': 'Game starting!',
            'secret_word_hint': 'A secret word has been set!'
        }, to=room)


@socketio.on('submit_guess')
def handle_submit_guess(data):
    """플레이어가 단어를 추측"""
    room = data['room']
    username = data['username']
    guess = data['guess']
    secret_word = games[room]['secret_word']

    # 유사도 계산
    similarity = calculate_similarity(secret_word, guess)

    if guess == secret_word:
        games[room]['scores'][username] += 10
        emit('guess_result', {
            'result': 'correct',
            'hint': f'The word is {secret_word}',
            'scores': games[room]['scores']
        }, to=room)
    else:
        emit('guess_result', {
            'result': 'incorrect',
            'hint': f'Similarity: {similarity:.2f}',
            'scores': games[room]['scores']
        }, to=room)


@socketio.on('leave_game')
def handle_leave_game(data):
    """플레이어가 게임 방을 나감"""
    room = data['room']
    username = data['username']
    leave_room(room)

    if room in games:
        games[room]['players'].remove(username)
        if not games[room]['players']:
            del games[room]  # 방에 아무도 없으면 방 삭제
        else:
            emit('player_left', {'username': username}, to=room)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8899)
