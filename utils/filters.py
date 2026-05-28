from datetime import datetime


def to_datetime(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def ucfirst_filter(value):
    if not value:
        return value
    try:
        return value[0].upper() + value[1:]
    except TypeError:
        return value


def strftime_filter(value, fmt="%d-%m-%Y"):
    return ucfirst_filter(to_datetime(value).strftime(fmt))


def to_iso_filter(value):
    return to_datetime(value).isoformat()


FILTERS = {
    "strftime": strftime_filter,
    "to_iso": to_iso_filter,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
