from flask import Flask, render_template, request
from metar import fetch_metar, decode, MetarError

app = Flask(__name__)


@app.route("/")
def index():
    code = request.args.get("code", "").strip()
    result = error = None
    if code:
        try:
            m = fetch_metar(code)
            result = {"plain": decode(m), "raw": m["rawOb"], "code": m["icaoId"]}
        except MetarError as e:
            error = str(e)
        except Exception:
            error = "Couldn't reach the weather service. Try again."
    return render_template("index.html", result=result, error=error, code=code)


if __name__ == "__main__":
    app.run(debug=True)
