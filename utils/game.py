import os
import random
from datetime import date

from flask import session

import data.gemeente_info as gemeente_info

EPOCH = date(2026, 5, 28)

HINTS = ["vlag_wapen", "kaart", "inwoners_oppervlakte", "provincie", "burgemeester"]

_shuffled_gemeenten = None


def _get_shuffled_gemeenten():
    global _shuffled_gemeenten
    if _shuffled_gemeenten is None:
        seed = os.environ["SHUFFLE_SEED"]
        gemeenten = list(gemeente_info.names())
        random.Random(seed).shuffle(gemeenten)
        _shuffled_gemeenten = gemeenten
    return _shuffled_gemeenten


def get_daily_gemeente():
    gemeenten = _get_shuffled_gemeenten()
    day = (date.today() - EPOCH).days
    return gemeenten[day % len(gemeenten)]


def get_state():
    today = str(date.today())
    if session.get("date") != today:
        session["date"] = today
        session["guesses"] = []
        session["result"] = "playing"
        session["hints_revealed"] = 1

    gemeente = get_daily_gemeente()
    info = gemeente_info.get(gemeente)
    hints_revealed = session["hints_revealed"]

    return {
        "date": session["date"],
        "guesses": session["guesses"],
        "result": session["result"],
        "gemeente": gemeente,
        "hints_revealed": hints_revealed,
        "max_hints": len(HINTS),
        "hints": _build_hints(info, hints_revealed),
        "has_data": bool(info),
        "day_number": (date.today() - EPOCH).days + 1,
        "error": None,
    }


def _build_hints(info, revealed):
    all_hints = [
        {"type": "vlag_wapen", "vlag": info.get("vlag"), "wapen": info.get("wapen")},
        {"type": "burgemeester", "burgemeester": info.get("burgemeester")},
        {
            "type": "inwoners_oppervlakte",
            "inwoners": info.get("inwoners"),
            "oppervlakte": info.get("oppervlakte"),
        },
        {"type": "provincie", "provincie": info.get("provincie")},
        {"type": "kaart", "kaart": info.get("kaart")},
    ]
    return all_hints[:revealed]


_valid_names = None


def _get_valid_names():
    global _valid_names
    if _valid_names is None:
        _valid_names = {n.lower() for n in gemeente_info.names()}
    return _valid_names


def submit_guess(guess):
    state = get_state()
    if state["result"] != "playing":
        return state

    guess = guess.strip()
    if guess.lower() not in _get_valid_names():
        state["error"] = "invalid"
        return state

    if any(g.lower() == guess.lower() for g in session["guesses"]):
        state["error"] = "duplicate"
        return state

    guesses = session["guesses"] + [guess]
    session["guesses"] = guesses

    if guess.lower() == state["gemeente"].lower():
        session["result"] = "won"
    else:
        hints_revealed = min(session["hints_revealed"] + 1, len(HINTS))
        session["hints_revealed"] = hints_revealed
        if len(guesses) >= len(HINTS):
            session["result"] = "lost"

    session.modified = True
    return get_state()
