import os
import pickle
from flask import Flask, jsonify, request, session, render_template, redirect, url_for, flash
from redis import Redis, ConnectionError, TimeoutError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

# Flask 초기화
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# Redis 설정 및 초기화
def get_redis_client():
    try:
        client = Redis(
            host=os.getenv('REDIS_HOST', 'redis'),  # localhost 대신 redis 사용
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=False,  # pickle 사용시 False로 설정
            socket_timeout=5
        )
        client.ping()
        print("Redis 연결 성공!")
        return client
    except (ConnectionError, TimeoutError) as e:
        print(f"Redis 연결 실패: {str(e)}")
        return None

redis_client = get_redis_client()

def check_redis():
    try:
        if redis_client is None:
            print("Redis 클라이언트가 초기화되지 않았습니다.")
            return
        
        redis_client.ping()
        print("Redis 연결 성공")
        
        # Redis에 저장된 모든 사용자 확인
        all_users = redis_client.hgetall("users")
        print(f"저장된 모든 사용자: {all_users}")
    except Exception as e:
        print(f"Redis 연결 확인 중 오류 발생: {str(e)}")
# 사용자 데이터 관리 클래스
class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
    
    def __str__(self):
        return f"User(username={self.username})"

def save_user(username, user_data):
    """사용자 정보를 Redis에 저장"""
    try:
        serialized_data = pickle.dumps(user_data)
        print(f"저장하는 데이터: {username}, {serialized_data}")  # 디버깅
        redis_client.hset("users", username, serialized_data)
        
        # 저장 직후 확인
        saved_data = redis_client.hget("users", username)
        print(f"저장된 데이터 확인: {saved_data}")  # 디버깅
    except Exception as e:
        print(f"사용자 저장 오류: {str(e)}")

def get_user(username):
    """Redis에서 사용자 정보를 가져오기"""
    try:
        user_data = redis_client.hget("users", username)
        print(f"불러온 데이터: {username}, {user_data}")  # 디버깅
        
        if user_data:
            try:
                if isinstance(user_data, str):
                    user_data = user_data.encode('latin1')
                user_obj = pickle.loads(user_data)
                print(f"변환된 사용자 객체: {user_obj.username}, {user_obj.password_hash}")  # 디버깅
                return user_obj
            except Exception as e:
                print(f"Pickle 변환 오류: {str(e)}")  # 디버깅
        return None
    except Exception as e:
        print(f"사용자 조회 오류: {str(e)}")
        return None

# API 엔드포인트들
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "사용자명과 비밀번호를 모두 입력해주세요"}), 400

    if get_user(username):
        return jsonify({"error": "이미 존재하는 사용자명입니다"}), 400

    user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    save_user(username, user)
    return jsonify({"message": "회원가입이 완료되었습니다"}), 201

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "사용자명과 비밀번호를 모두 입력해주세요"}), 400

    user = get_user(username)
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "잘못된 사용자명 또는 비밀번호입니다"}), 401

    session['user_id'] = username
    return jsonify({"message": "로그인 성공"}), 200

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({"message": "로그아웃 되었습니다"}), 200

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "username": session['user_id']
        })
    return jsonify({"authenticated": False})

# 웹 인터페이스 라우트들
@app.route('/')
def index():
    username = session.get('user_id')
    # 빈 rooms 딕셔너리 전달
    rooms = {}  # 또는 실제 방 목록을 가져오는 로직
    return render_template('index.html', username=username, rooms=rooms)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        print(f"로그인 시도: username={username}")  # 디버깅

        if not username or not password:
            flash("사용자명과 비밀번호를 모두 입력해주세요")
            return redirect(url_for('login'))

        user = get_user(username)
        print(f"조회된 사용자: {user}")  # 디버깅

        if not user:
            print("사용자를 찾을 수 없음")  # 디버깅
            flash("잘못된 사용자명 또는 비밀번호입니다")
            return redirect(url_for('login'))

        if not check_password_hash(user.password_hash, password):
            print("비밀번호 불일치")  # 디버깅
            flash("잘못된 사용자명 또는 비밀번호입니다")
            return redirect(url_for('login'))

        session['user_id'] = username
        return redirect(url_for('index'))

    return render_template('login.html')

# 회원가입 함수 수정
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        print(f"회원가입 시도: username={username}")  # 디버깅

        if not username or not password:
            flash("사용자명과 비밀번호를 모두 입력해주세요")
            return redirect(url_for('register'))

        existing_user = get_user(username)
        print(f"기존 사용자 확인: {existing_user}")  # 디버깅

        if existing_user:
            flash("이미 존재하는 사용자명입니다")
            return redirect(url_for('register'))

        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        save_user(username, user)
        print(f"새 사용자 저장 완료: {user}")  # 디버깅
        flash("회원가입이 완료되었습니다")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)