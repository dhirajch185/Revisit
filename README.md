# METAR Reader

Type an airport code, get the current weather in plain English.

A METAR is the coded weather report pilots use, like
`METAR KJFK 282051Z 36009KT 8SM FEW008 BKN012 OVC029 16/14 A2986`.
This small Flask app fetches the latest one for any airport and translates it:

> Mostly cloudy at 1200 ft, 61°F, wind 10 mph from the N, visibility 8 miles, altimeter 29.86 inHg (MVFR conditions).

Along with the sentence you get a strip of key facts (sky, wind, visibility,
temperature, altimeter), the flight category color-coded the way aviation
weather charts do it (VFR, MVFR, IFR, LIFR), and the raw report.

Data comes live from the [Aviation Weather Center](https://aviationweather.gov/data/api/) API. No API key needed.

## Install

Requires Python 3.9 or newer.

```bash
git clone https://github.com/dhirajch185/Revisit.git
cd Revisit
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000 and enter an ICAO code such as `KHIO`, `KJFK` or `EGLL`.

`python app.py` starts Flask's development server with debug mode on. It is
meant for local use only. To serve it publicly, run it behind a production
WSGI server instead, for example `pip install gunicorn` then
`gunicorn app:app`.

## Test

```bash
python test_metar.py
```

Prints `all tests passed (15)` when everything works, or a traceback pointing
at the failing assertion. No pytest or other test dependency is needed; the
script runs every `test_*` function in the file.

The tests never touch the network. There are two kinds:

- **Decoding tests** call the functions in `metar.py` directly: unit
  conversions, compass points, weather codes such as `+TSRA` and `VCTS`,
  picking the cloud ceiling, and input validation.
- **Route tests** use Flask's test client against `app.py`, with
  `fetch_metar` mocked to return hand-built readings shaped like the
  Aviation Weather Center API response. They check the rendered page for
  VFR, MVFR, IFR and LIFR conditions, gusts, variable and calm wind,
  the empty form, and each error message.

To add a case, copy one of the mock readings (for example `MVFR_KJFK` in
`test_metar.py`), change the values, and assert on the text you expect to see.

## How it works

| File | Role |
|------|------|
| `metar.py` | Fetches the report and decodes it. No Flask dependency. |
| `app.py` | One route, `/`, that reads the `code` query parameter. |
| `templates/index.html` | The page: form, result and inline CSS. |
| `test_metar.py` | Tests for the decoding logic and the route. |

Values are converted for a US audience: °C to °F, knots to mph, hPa to inHg.
To decode more weather phenomena, extend the lookup tables at the top of
`metar.py`.

## Limitations

- Only airports that publish METARs work; small fields without weather
  reporting return "No METAR found".
- Remarks (`RMK ...`) in the raw report are shown but not decoded.
- It shows the latest report only, not forecasts (TAFs) or history.

## License

[MIT](LICENSE)
