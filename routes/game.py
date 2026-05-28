from flask import Blueprint, render_template, request

import data.gemeente_info as gemeente_info
from utils.game import get_state, submit_guess

game_bp = Blueprint("game", __name__)


@game_bp.get("/")
def index():
    return render_template(
        "game/index.jinja", **get_state(), all_gemeenten=gemeente_info.names()
    )


@game_bp.post("/guess")
def guess():
    guess = request.form.get("guess", "")
    state = submit_guess(guess)
    return render_template(
        "game/board.jinja", **state, all_gemeenten=gemeente_info.names()
    )
