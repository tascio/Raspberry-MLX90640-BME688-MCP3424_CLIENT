from flask import Flask
from flask_cors import CORS
from main.logger import logger
from main.views import views_bp
from flask_socketio import SocketIO
from main.models import Termocamera, Threshold, MLX90640Hub, socketio as models_socketio
from main.config import cfg
import ast

socketio = SocketIO(async_mode='eventlet')

def create_app():
    try:
        app = Flask(__name__, template_folder='../templates', static_folder='../static')
        CORS(app)
        socketio.init_app(app, cors_allowed_origins="*")

        import main.models
        main.models.socketio = socketio

        app.register_blueprint(views_bp)

        app.config['SERVER_REST'] = f"http://{cfg['API_SERVER']['IP_REST']}:{cfg['API_SERVER']['PORT_REST']}"
        app.config['SERVER_SOCK'] = f"http://{cfg['API_SERVER']['IP_SOCK']}:{cfg['API_SERVER']['PORT_SOCK']}"
        app.config['WA'] = ast.literal_eval(cfg['WET_ARRAY']['wa'])

        Termocamera.VMIN = float(cfg['TERMO_CAMERA']['VMIN'])
        Termocamera.VMAX = float(cfg['TERMO_CAMERA']['VMAX'])

        Threshold.status = False

        MLX90640Hub(app)

    except Exception as e:
        logger.critical(f'INITIALIZING ERROR {e}')
        print('create app error ',str(e))

    return app