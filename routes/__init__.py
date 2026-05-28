from .game import game_bp


def register_routes(app):
    app.register_blueprint(game_bp)
