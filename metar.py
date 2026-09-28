"""Fetch METAR from aviationweather.gov and decode to plain English."""
import requests

API_URL = "https://aviationweather.gov/api/data/metar"

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

SKY = {
    "SKC": "clear skies", "CLR": "clear skies", "CAVOK": "clear skies",
    "FEW": "a few clouds", "SCT": "scattered clouds",
    "BKN": "mostly cloudy", "OVC": "overcast", "VV": "sky obscured",
}

WX_INTENSITY = {"-": "light ", "+": "heavy "}
CEILING_COVERS = {"BKN", "OVC", "VV"}
WX_CODES = {
    "MI": "shallow", "PR": "partial", "BC": "patchy", "DR": "drifting",
    "BL": "blowing", "SH": "showers of", "TS": "thunderstorm with",
    "FZ": "freezing", "DZ": "drizzle", "RA": "rain", "SN": "snow",
    "SG": "snow grains", "IC": "ice crystals", "PL": "ice pellets",
    "GR": "hail", "GS": "small hail", "UP": "unknown precipitation",
    "BR": "mist", "FG": "fog", "FU": "smoke", "VA": "volcanic ash",
    "DU": "dust", "SA": "sand", "HZ": "haze", "PY": "spray",
    "PO": "dust whirls", "SQ": "squalls", "FC": "funnel cloud",
    "SS": "sandstorm", "DS": "duststorm", "VC": "nearby",
}


class MetarError(Exception):
    pass


def fetch_metar(icao):
    icao = icao.strip().upper()
    if not (icao.isascii() and icao.isalnum()) or not (3 <= len(icao) <= 5):
        raise MetarError(f"'{icao}' doesn't look like a valid airport code.")
    resp = requests.get(API_URL, params={"ids": icao, "format": "json"}, timeout=10)
    resp.raise_for_status()
    # The API answers 204 with an empty body for unknown stations.
    data = resp.json() if resp.content else None
    if not data:
        raise MetarError(f"No METAR found for '{icao}'. Airport codes are 4 letters, e.g. KHIO.")
    return data[0]


def c_to_f(c):
    return c * 9 / 5 + 32


def compass_point(deg):
    return COMPASS[round(deg / 22.5) % 16]


def decode_wx_string(wx_string):
    if not wx_string:
        return []
    phrases = []
    for token in wx_string.split():
        intensity = ""
        if token and token[0] in WX_INTENSITY:
            intensity = WX_INTENSITY[token[0]]
            token = token[1:]
        parts = [WX_CODES.get(token[i:i + 2], token[i:i + 2])
                 for i in range(0, len(token), 2)]
        phrases.append(intensity + " ".join(parts))
    return phrases


def sky_layer(m):
    """The layer that matters for flying: the ceiling (lowest BKN/OVC/VV), else the lowest layer."""
    clouds = m.get("clouds") or []
    ceiling = [c for c in clouds if c.get("cover") in CEILING_COVERS]
    layers = ceiling or clouds
    return min(layers, key=lambda c: c.get("base") or 0) if layers else None


def decode(m):
    """Turn a parsed METAR dict (aviationweather.gov JSON) into a plain-English sentence."""
    parts = []

    wx = decode_wx_string(m.get("wxString"))
    if wx:
        parts.append(", ".join(wx))

    layer = sky_layer(m)
    if layer:
        sky_desc = SKY.get(layer.get("cover"), layer.get("cover", "unknown sky"))
        parts.append(f"{sky_desc} at {layer['base']} ft" if layer.get("base") else sky_desc)
    else:
        parts.append(SKY.get(m.get("cover"), "clear skies"))

    if m.get("temp") is not None:
        parts.append(f"{round(c_to_f(m['temp']))}°F")

    wspd = m.get("wspd")
    if wspd:
        mph = round(wspd * 1.15078)
        wdir = m.get("wdir")
        if isinstance(wdir, (int, float)):
            wind = f"wind {mph} mph from the {compass_point(wdir)}"
        else:
            wind = f"wind {mph} mph, variable direction"
        gust = m.get("wgst")
        if gust:
            wind += f", gusting to {round(gust * 1.15078)} mph"
        parts.append(wind)
    else:
        parts.append("calm wind")

    visib = m.get("visib")
    if visib is not None:
        parts.append(f"visibility {visib} miles")

    altim = m.get("altim")
    if altim:
        parts.append(f"altimeter {round(altim / 33.8639, 2)} inHg")

    cat = m.get("fltCat")
    summary = ", ".join(parts)
    if cat:
        summary += f" ({cat} conditions)"
    return summary[0:1].upper() + summary[1:] + "."


def facts(m):
    """Short labelled values for the result strip. Missing data is left out."""
    out = []
    layer = sky_layer(m)
    if layer:
        sky = SKY.get(layer.get("cover"), layer.get("cover"))
        out.append(("Sky", f"{sky} at {layer['base']:,} ft" if layer.get("base") else sky))
    wspd, wdir = m.get("wspd"), m.get("wdir")
    if wspd:
        where = f"from the {compass_point(wdir)}" if isinstance(wdir, (int, float)) else "variable"
        out.append(("Wind", f"{round(wspd * 1.15078)} mph {where}"))
    else:
        out.append(("Wind", "calm"))
    if m.get("visib") is not None:
        out.append(("Visibility", f"{m['visib']} mi"))
    if m.get("temp") is not None:
        out.append(("Temperature", f"{round(c_to_f(m['temp']))}°F"))
    if m.get("altim"):
        out.append(("Altimeter", f"{m['altim'] / 33.8639:.2f} inHg"))
    return out
