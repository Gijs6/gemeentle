from flask import Blueprint, abort, current_app, redirect, render_template, request, session, url_for

import data.gemeente_info as gemeente_info
from utils.game import get_state, gemeente_for_day, submit_guess

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


@game_bp.post("/dev/game")
def dev_game():
    if not current_app.debug:
        abort(404)

    action = request.form.get("action", "day")
    if action == "reset":
        session.pop("dev_gemeente", None)
    elif action == "gemeente":
        naam = request.form.get("gemeente", "").strip()
        match = next((g for g in gemeente_info.names() if g.lower() == naam.lower()), None)
        if match:
            session["dev_gemeente"] = match
    else:
        day = int(request.form.get("day", 1)) - 1
        session["dev_gemeente"] = gemeente_for_day(day)

    session.pop("date", None)
    session.pop("gemeente", None)
    session.modified = True
    return redirect(url_for("game.index"))
