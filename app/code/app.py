from main import create_app
from main.logger import logger

try:
    app = create_app()
    logger.info('App started')
except Exception as e:
    logger.critical(f'App crashed {e}')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5080, debug=True)
