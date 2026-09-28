import requests
from flask import Flask, render_template, request
from metar import fetch_metar, decode, facts, MetarError

app = Flask(__name__)


@app.route("/")
def index():
    code = request.args.get("code", "").strip()
    result = error = None
    if code:
        try:
            m = fetch_metar(code)
            result = {"plain": decode(m), "raw": m["rawOb"], "code": m["icaoId"],
                      "name": m.get("name"), "cat": m.get("fltCat"), "facts": facts(m)}
        except MetarError as e:
            error = str(e)
        except requests.RequestException:
            error = "Couldn't reach the weather service. Try again in a moment."
        except Exception:
            app.logger.exception("decode failed for %r", code)
            error = "Something went wrong reading that report. Try another airport."
    return render_template("index.html", result=result, error=error, code=code)


if __name__ == "__main__":
    app.run(debug=True)
