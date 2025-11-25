from main.models import mlx90640_view


def main(app):
    app.config['mlx90640_websocket'] = mlx90640_view(app.config['SERVER_SOCK'])

