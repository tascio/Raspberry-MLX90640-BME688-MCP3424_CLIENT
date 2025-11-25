from flask import Flask
from main.logger import logger
from main.views import views_bp
from main.models import Termocamera, Threshold
from main.config import cfg
from main import websocket
import ast

def create_app():
    try:
        app = Flask(__name__, template_folder='../templates', static_folder='../static')
        app.register_blueprint(views_bp)

        app.config['SERVER_REST'] = f"http://{cfg['API_SERVER']['IP_REST']}:{cfg['API_SERVER']['PORT_REST']}"
        app.config['SERVER_SOCK'] = f"http://{cfg['API_SERVER']['IP_SOCK']}:{cfg['API_SERVER']['PORT_SOCK']}"
        app.config['WA'] = ast.literal_eval(cfg['WET_ARRAY']['wa'])

        Termocamera.VMIN = float(cfg['TERMO_CAMERA']['VMIN'])
        Termocamera.VMAX = float(cfg['TERMO_CAMERA']['VMAX'])

        Threshold.status = False

        websocket.main(app)

    except Exception as e:
        logger.critical(f'INITIALIZING ERROR {e}')
        print('create app error ',str(e))

    return app