from gevent import monkey
monkey.patch_all()

from semantle import app, socketio

# Flask-SocketIO 애플리케이션
application = app

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000) 