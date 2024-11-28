import multiprocessing

bind = "0.0.0.0:5000"
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
workers = 1
worker_connections = 1000
timeout = 120
keepalive = 2

# SSL 설정
keyfile = None
certfile = None

# 로깅 설정
loglevel = 'debug'
accesslog = '-'
errorlog = '-'

preload_app = True
reload = True 