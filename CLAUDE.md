# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Tiny Flask app: user enters ICAO airport code, app fetches live METAR from aviationweather.gov and renders a plain-English decoded weather summary alongside the raw METAR string.

## Commands

```bash
pip install -r requirements.txt   # deps: flask, requests
python app.py                     # run dev server (debug=True), http://127.0.0.1:5000
python test_metar.py              # run tests (plain asserts, no pytest) - prints "all tests passed"
```

No pytest, no linter, no build step configured in this repo.

## Architecture

Three files carry all logic:

- **`metar.py`** — pure logic, no Flask dependency. `fetch_metar(icao)` validates the code and hits the aviationweather.gov JSON API, returning the raw dict for the first match. `decode(m)` turns that dict into one plain-English sentence (sky, temp, wind, visibility, altimeter, flight category). Lookup tables at module level (`COMPASS`, `SKY`, `WX_CODES`, `WX_INTENSITY`) drive the decoding — extend these when adding new METAR phenomena rather than adding branching logic. `decode_wx_string` tokenizes present-weather codes (e.g. `+TSRA` → `heavy thunderstorm with rain`) two chars at a time, prefixed by an intensity symbol.
- **`app.py`** — single `/` route. Reads `code` query param, calls `fetch_metar`/`decode`, catches `MetarError` for user-facing messages and any other exception as a generic "couldn't reach service" fallback.
- **`templates/index.html`** — single Jinja template, inline CSS, renders the form + result/error.

All units are converted from the API's metric values to US units for display (°C→°F via `c_to_f`, m/s→mph via `*1.15078`, hPa altimeter→inHg via `/33.8639`).

`test_metar.py` tests `metar.py` functions directly against hand-built dict fixtures (shaped like aviationweather.gov API responses) — no network calls, no Flask test client.
