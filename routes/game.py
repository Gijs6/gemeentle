from datetime import date

import requests as http
from flask import (
    Blueprint,
    abort,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import data.gemeente_info as gemeente_info
from utils.game import (
    EPOCH,
    get_archive_state,
    get_state,
    gemeente_for_day,
    submit_archive_guess,
    submit_guess,
)

ALLOWED_IMG_KINDS = {"vlag", "wapen", "kaart"}


def proxy_image(url):
    try:
        r = http.get(url, timeout=10, headers={"User-Agent": "gemeentle/1.0"})
        r.raise_for_status()
    except Exception:
        abort(502)
    content_type = r.headers.get("Content-Type", "image/svg+xml")
    resp = make_response(r.content)
    resp.headers["Content-Type"] = content_type
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

game_bp = Blueprint("game", __name__)


def game_response(template, state, status=200):
    response = make_response(render_template(template, **state), status)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    if request.headers.get("HX-Request"):
        response.headers["HX-Push-Url"] = "false"
    return response


def guess_status(error):
    if error == "invalid":
        return 422
    if error == "duplicate":
        return 409
    return 200


@game_bp.get("/")
def index():
    return game_response(
        "game/index.jinja", {**get_state(), "all_gemeenten": gemeente_info.names()}
    )


@game_bp.post("/guess")
def guess():
    state = submit_guess(request.form.get("guess", ""))
    return game_response("game/board.jinja", state, guess_status(state["error"]))


@game_bp.get("/archief/<int:day>")
def archief_dag(day):
    today_day = (date.today() - EPOCH).days
    if day >= today_day or day < 0:
        return redirect(url_for("game.index"), 302)
    state = get_archive_state(day)
    return game_response(
        "game/archief_dag.jinja",
        {**state, "all_gemeenten": gemeente_info.names(), "today_day": today_day},
    )


@game_bp.post("/archief/<int:day>/guess")
def archief_guess(day):
    today_day = (date.today() - EPOCH).days
    if day >= today_day or day < 0:
        return redirect(url_for("game.index"), 302)
    state = submit_archive_guess(day, request.form.get("guess", ""))
    return game_response("game/board.jinja", state, guess_status(state["error"]))


@game_bp.post("/dev/game")
def dev_game():
    if not current_app.debug:
        abort(404)

    action = request.form.get("action", "day")
    if action == "reset":
        session.pop("dev_gemeente", None)
    elif action == "gemeente":
        naam = request.form.get("gemeente", "").strip()
        match = next(
            (g for g in gemeente_info.names() if g.lower() == naam.lower()), None
        )
        if match:
            session["dev_gemeente"] = match
    else:
        day = int(request.form.get("day", 1)) - 1
        session["dev_gemeente"] = gemeente_for_day(day)

    session.pop("date", None)
    session.pop("gemeente", None)
    session.modified = True
    return redirect(url_for("game.index"), 303)


@game_bp.get("/img/<kind>")
def img(kind):
    if kind not in ALLOWED_IMG_KINDS:
        abort(404)
    gemeente = session.get("gemeente")
    if not gemeente:
        abort(404)
    url = gemeente_info.get(gemeente).get(kind)
    if not url:
        abort(404)
    return proxy_image(url)


@game_bp.get("/archief/<int:day>/img/<kind>")
def archief_img(day, kind):
    if kind not in ALLOWED_IMG_KINDS:
        abort(404)
    today_day = (date.today() - EPOCH).days
    if day >= today_day or day < 0:
        abort(404)
    url = gemeente_info.get(gemeente_for_day(day)).get(kind)
    if not url:
        abort(404)
    return proxy_image(url)


@game_bp.get("/archief")
def archief():
    if not request.headers.get("HX-Request"):
        return redirect(url_for("game.index"), 302)

    from datetime import timedelta

    today_day = (date.today() - EPOCH).days
    history = session.get("history", {})

    months = []
    current_key = None

    for day in range(today_day):
        d = EPOCH + timedelta(days=day)
        month_key = (d.year, d.month)
        if month_key != current_key:
            current_key = month_key
            months.append({"month_date": d, "weekday_offset": d.weekday(), "days": []})

        entry = history.get(str(d))
        months[-1]["days"].append(
            {
                "day": day,
                "date": d,
                "day_number": day + 1,
                "result": entry["result"] if entry else None,
                "guesses": entry["guesses"] if entry else None,
            }
        )

    response = make_response(render_template("game/archief.jinja", months=months))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie"
    return response
