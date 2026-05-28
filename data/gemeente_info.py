import json
import os

_JSON_PATH = os.path.join(os.path.dirname(__file__), "gemeenten.json")

_cache = None


def load():
    global _cache
    if _cache is None:
        if os.path.exists(_JSON_PATH):
            with open(_JSON_PATH, encoding="utf-8") as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache


def get(naam):
    return load().get(naam, {})


def names():
    return list(load().keys())
