FROM python:3.9-slim

# Flask 앱 환경변수 설정
ENV FLASK_APP=app
ENV FLASK_ENV=production

WORKDIR /app

# 시스템 의존성 설치 (Rust 포함)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Rust 설치 (단어 유사도 계산에 필요한 의존성을 위해)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 필요한 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 데이터 디렉토리 생성 (단어 벡터 데이터용)
RUN mkdir -p /app/data/near

# 애플리케이션 코드 복사
COPY . /app/

# 데이터 파일 복사
COPY data/ /app/data/

# 볼륨 마운트 포인트 설정 (단어 데이터 및 게임 상태 저장용)
VOLUME ["/app/data"]

# WebSocket 통신을 위한 포트 노출
EXPOSE 5000
# 템플릿 디렉토리 복사 추가
COPY templates ./templates
COPY semantle.py .

# Gunicorn으로 실행 (eventlet 워커를 사용하여 WebSocket 지원)
CMD ["python", "semantle.py"]