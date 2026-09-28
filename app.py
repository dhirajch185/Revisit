"""Flask front end for the METAR reader.

Serves a single page: the user enters an ICAO airport code, and the app
fetches the latest METAR and renders a plain-English summary next to the
raw report. All weather logic lives in ``metar.py``.
"""
import requests
from flask import Flask, render_template, request

from metar import MetarError, decode, facts, fetch_metar

app = Flask(__name__)


@app.route("/")
def index():
    """Render the search form, plus the decoded report when ``?code=`` is given.

    Errors become user-facing messages instead of raising: invalid or
    unknown airport codes, network failures and unexpected decoding
    errors each get their own message.
    """
    code = request.args.get("code", "").strip()
    result = error = None
    if code:
        try:
            m = fetch_metar(code)
            result = {
                "plain": decode(m),
                "raw": m["rawOb"],
                "code": m["icaoId"],
                "name": m.get("name"),
                "cat": m.get("fltCat"),  # VFR/MVFR/IFR/LIFR, drives the styling
                "facts": facts(m),
            }
        except MetarError as e:
            # Expected failures (bad code, no report): message is safe to show.
            error = str(e)
        except requests.RequestException:
            error = "Couldn't reach the weather service. Try again in a moment."
        except Exception:
            # Anything else is a bug: log the traceback, keep the page usable.
            app.logger.exception("decode failed for %r", code)
            error = "Something went wrong reading that report. Try another airport."
    return render_template("index.html", result=result, error=error, code=code)


if __name__ == "__main__":
    # Development server only; never expose debug mode publicly.
    app.run(debug=True)
