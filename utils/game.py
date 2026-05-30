import os
import random
from datetime import date, timedelta

from flask import current_app, session

import data.gemeente_info as gemeente_info

EPOCH = date(2026, 5, 28)

HINTS = [
    "vlag_wapen",
    "kaart",
    "inwoners_oppervlakte",
    "provincie",
    "buren",
    "burgemeester",
]

_shuffled_gemeenten = None


def get_shuffled_gemeenten():
    global _shuffled_gemeenten
    if _shuffled_gemeenten is None:
        seed = os.environ["SHUFFLE_SEED"]
        gemeenten = list(gemeente_info.names())
        random.Random(seed).shuffle(gemeenten)
        _shuffled_gemeenten = gemeenten
    return _shuffled_gemeenten


def get_revealed_indices(gemeente, hints_revealed, max_hints):
    letter_count = sum(1 for c in gemeente if c not in (" ", "-", "'"))
    if letter_count <= 1:
        return set()
    positions = list(range(1, letter_count))
    random.Random(gemeente).shuffle(positions)
    wrong_guesses = hints_revealed - 1
    if wrong_guesses < 2:
        return set()
    count = round(len(positions) * (wrong_guesses - 1) / (max_hints * 2))
    return set(positions[:count])


def get_daily_gemeente():
    gemeenten = get_shuffled_gemeenten()
    if current_app.debug and "dev_gemeente" in session:
        return session["dev_gemeente"]
    day = (date.today() - EPOCH).days
    return gemeenten[day % len(gemeenten)]


def gemeente_for_day(day):
    gemeenten = get_shuffled_gemeenten()
    return gemeenten[day % len(gemeenten)]


def get_state():
    today = str(date.today())
    gemeente = get_daily_gemeente()

    if session.get("date") != today or session.get("gemeente") != gemeente:
        session["date"] = today
        session["gemeente"] = gemeente
        session["guesses"] = []
        session["result"] = "playing"
        session["hints_revealed"] = 1
    info = gemeente_info.get(gemeente)
    hints_revealed = session["hints_revealed"]

    return {
        "date": session["date"],
        "guesses": session["guesses"],
        "result": session["result"],
        "gemeente": gemeente,
        "hints_revealed": hints_revealed,
        "max_hints": len(HINTS),
        "hints": build_hints(info, hints_revealed),
        "has_data": bool(info.get("vlag") or info.get("wapen")),
        "day_number": (date.today() - EPOCH).days + 1,
        "revealed_indices": get_revealed_indices(gemeente, hints_revealed, len(HINTS)),
        "error": None,
        "is_archive": False,
        "archive_day": None,
    }


def get_archive_state(day):
    gemeente = gemeente_for_day(day)
    session_key = f"archive_{day}"

    if session_key not in session:
        session[session_key] = {"guesses": [], "result": "playing", "hints_revealed": 1}

    game_data = session[session_key]
    info = gemeente_info.get(gemeente)

    return {
        "date": str(EPOCH + timedelta(days=day)),
        "guesses": game_data["guesses"],
        "result": game_data["result"],
        "gemeente": gemeente,
        "hints_revealed": game_data["hints_revealed"],
        "max_hints": len(HINTS),
        "hints": build_hints(info, game_data["hints_revealed"]),
        "has_data": bool(info.get("vlag") or info.get("wapen")),
        "day_number": day + 1,
        "revealed_indices": get_revealed_indices(
            gemeente, game_data["hints_revealed"], len(HINTS)
        ),
        "error": None,
        "is_archive": True,
        "archive_day": day,
    }


def record_result(date_str, result, guesses):
    history = session.get("history", {})
    history[date_str] = {"result": result, "guesses": guesses}
    session["history"] = history


def submit_archive_guess(day, guess):
    state = get_archive_state(day)
    session_key = f"archive_{day}"
    game_data = session[session_key]

    if state["result"] != "playing":
        return state

    guess = guess.strip()
    if guess.lower() not in get_valid_names():
        state["error"] = "invalid"
        return state

    if any(g.lower() == guess.lower() for g in game_data["guesses"]):
        state["error"] = "duplicate"
        return state

    guesses = game_data["guesses"] + [guess]
    game_data["guesses"] = guesses
    date_str = str(EPOCH + timedelta(days=day))

    if guess.lower() == state["gemeente"].lower():
        game_data["result"] = "won"
        record_result(date_str, "won", len(guesses))
    else:
        game_data["hints_revealed"] = min(game_data["hints_revealed"] + 1, len(HINTS))
        if len(guesses) >= len(HINTS):
            game_data["result"] = "lost"
            record_result(date_str, "lost", len(guesses))

    session[session_key] = game_data
    session.modified = True
    return get_archive_state(day)


def build_hints(info, revealed):
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
        {"type": "buren", "buren": info.get("buren", [])},
    ]
    return all_hints[:revealed]


_valid_names = None


def get_valid_names():
    global _valid_names
    if _valid_names is None:
        _valid_names = {n.lower() for n in gemeente_info.names()}
    return _valid_names


def submit_guess(guess):
    state = get_state()
    if state["result"] != "playing":
        return state

    guess = guess.strip()
    if guess.lower() not in get_valid_names():
        state["error"] = "invalid"
        return state

    if any(g.lower() == guess.lower() for g in session["guesses"]):
        state["error"] = "duplicate"
        return state

    guesses = session["guesses"] + [guess]
    session["guesses"] = guesses

    if guess.lower() == state["gemeente"].lower():
        session["result"] = "won"
        record_result(session["date"], "won", len(guesses))
    else:
        hints_revealed = min(session["hints_revealed"] + 1, len(HINTS))
        session["hints_revealed"] = hints_revealed
        if len(guesses) >= len(HINTS):
            session["result"] = "lost"
            record_result(session["date"], "lost", len(guesses))

    session.modified = True
    return get_state()
