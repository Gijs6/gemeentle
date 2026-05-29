import locale
import os

from dotenv import load_dotenv
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from routes import register_routes
from utils.filters import register_filters

locale.setlocale(locale.LC_TIME, "nl_NL.UTF-8")


load_dotenv(override=True)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(100).hex())

register_filters(app)
register_routes(app)


@app.errorhandler(404)
def not_found(_e):
    return render_template(
        "error.jinja",
        code=404,
        title="Not Found",
        description="Deze pagina bestaat niet.",
    ), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template(
        "error.jinja",
        code=500,
        title="Server Error",
        description="Er is iets misgegaan. Probeer het later opnieuw.",
    ), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
