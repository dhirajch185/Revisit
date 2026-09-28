from unittest import mock
from metar import decode, decode_wx_string, compass_point, c_to_f, fetch_metar, MetarError, facts

def test_decode_clear():
    m = {"temp": 16.7, "wdir": 350, "wspd": 3, "visib": "10+", "altim": 1019.7,
         "clouds": [{"cover": "OVC", "base": 3300}], "fltCat": "VFR", "wxString": None}
    s = decode(m)
    assert "62" in s          # 16.7C -> 62F
    assert "mph" in s and "N" in s
    assert "10+" in s
    assert s.endswith(".")

def test_decode_rain_gust():
    m = {"temp": 10, "wdir": 200, "wspd": 15, "wgst": 25, "visib": 3, "altim": 1000,
         "clouds": [], "cover": "SKC", "wxString": "-RA"}
    s = decode(m)
    assert "light rain" in s.lower()
    assert "gusting" in s

def test_compass_and_temp():
    assert compass_point(0) == "N"
    assert compass_point(90) == "E"
    assert round(c_to_f(0)) == 32

def test_wx_string_thunderstorm():
    assert decode_wx_string("+TSRA") == ["heavy thunderstorm with rain"]
    assert decode_wx_string(None) == []

def test_ceiling_not_highest_layer():
    m = {"clouds": [{"cover": "FEW", "base": 2000}, {"cover": "BKN", "base": 25000}]}
    assert "mostly cloudy at 25000 ft" in decode(m).lower()
    m = {"clouds": [{"cover": "FEW", "base": 800}, {"cover": "BKN", "base": 1200}, {"cover": "OVC", "base": 2900}]}
    assert "mostly cloudy at 1200 ft" in decode(m).lower()

def test_vicinity_and_variable_wind():
    assert decode_wx_string("VCTS") == ["nearby thunderstorm with"]
    assert "variable direction" in decode({"wspd": 5, "wdir": "VRB"})
    assert "calm wind" in decode({"wspd": 0})

def test_facts():
    f = dict(facts({"wspd": 0, "temp": 0, "altim": 1013.25, "visib": "10+"}))
    assert f["Wind"] == "calm" and f["Temperature"] == "32°F" and f["Visibility"] == "10+ mi"

def test_fetch_errors():
    for bad in ("", "AB", "TOOLONG", "K H"):
        try:
            fetch_metar(bad)
            assert False, bad
        except MetarError:
            pass
    with mock.patch("metar.requests.get") as get:
        get.return_value.content = b""
        try:
            fetch_metar("ZZZZ")
            assert False
        except MetarError as e:
            assert "No METAR" in str(e)

# --- app.py: route tests. fetch_metar is mocked with API-shaped readings, so
# the route, decode(), facts() and the template run together without network.

import requests
from app import app

MVFR_KJFK = {   # real KJFK report: multi-layer clouds, ceiling is BKN012
    "icaoId": "KJFK", "name": "New York/JF Kennedy Intl, NY, US", "fltCat": "MVFR",
    "rawOb": "METAR KJFK 282051Z 36009KT 8SM FEW008 BKN012 OVC029 16/14 A2986 RMK AO2",
    "temp": 16.1, "wdir": 360, "wspd": 9, "visib": 8, "altim": 1011.3, "cover": "OVC",
    "clouds": [{"cover": "FEW", "base": 800}, {"cover": "BKN", "base": 1200},
               {"cover": "OVC", "base": 2900}],
}
VFR_KHIO = {    # clear, light wind, unlimited visibility
    "icaoId": "KHIO", "name": "Portland/Hillsboro, OR, US", "fltCat": "VFR",
    "rawOb": "METAR KHIO 282053Z 35006KT 10SM CLR 22/09 A3000",
    "temp": 22, "wdir": 350, "wspd": 6, "visib": "10+", "altim": 1015.9, "cover": "CLR",
    "clouds": [],
}
IFR_STORM = {   # heavy thunderstorm, gusts, low ceiling
    "icaoId": "KATL", "name": "Atlanta/Hartsfield, GA, US", "fltCat": "IFR",
    "rawOb": "METAR KATL 282052Z 24018G32KT 2 1/2SM +TSRA SCT015 OVC025 24/22 A2977",
    "temp": 24, "wdir": 240, "wspd": 18, "wgst": 32, "visib": 2.5, "altim": 1008,
    "wxString": "+TSRA", "cover": "OVC",
    "clouds": [{"cover": "SCT", "base": 1500}, {"cover": "OVC", "base": 2500}],
}
LIFR_FOG = {    # variable wind, fog, vertical visibility only
    "icaoId": "KSFO", "name": "San Francisco Intl, CA, US", "fltCat": "LIFR",
    "rawOb": "METAR KSFO 282056Z VRB03KT 1/4SM FG VV001 12/12 A3006",
    "temp": 12, "wdir": "VRB", "wspd": 3, "visib": 0.25, "altim": 1018,
    "wxString": "FG", "cover": "VV", "clouds": [{"cover": "VV", "base": 100}],
}
CALM = dict(VFR_KHIO, wspd=0, wdir=0)


def page(code="KXXX", metar=None, side_effect=None):
    """GET / with fetch_metar mocked to return `metar` or raise `side_effect`."""
    with mock.patch("app.fetch_metar", return_value=metar, side_effect=side_effect):
        with mock.patch.object(app.logger, "exception"):  # keep test output quiet
            return app.test_client().get("/", query_string={"code": code}).get_data(as_text=True)


def test_route_mvfr_multilayer():
    html = page("KJFK", MVFR_KJFK)
    assert "Mostly cloudy at 1200 ft" in html       # ceiling, not top layer
    assert "61°F" in html and "wind 10 mph from the N" in html
    assert "visibility 8 miles" in html and "29.86 inHg" in html
    assert 'class="report MVFR"' in html and "(MVFR conditions)" in html
    assert MVFR_KJFK["rawOb"] in html and "New York/JF Kennedy" in html

def test_route_vfr_clear():
    html = page("KHIO", VFR_KHIO)
    assert "Clear skies" in html and "72°F" in html
    assert "wind 7 mph from the N" in html and "visibility 10+ miles" in html
    assert "30.00 inHg" in html and 'class="report VFR"' in html

def test_route_ifr_thunderstorm_gusts():
    html = page("KATL", IFR_STORM)
    assert "heavy thunderstorm with rain" in html.lower()
    assert "wind 21 mph from the WSW, gusting to 37 mph" in html
    assert "overcast at 2500 ft" in html and "75°F" in html
    assert 'class="report IFR"' in html

def test_route_lifr_fog_variable_wind():
    html = page("KSFO", LIFR_FOG)
    assert "fog" in html.lower() and "sky obscured at 100 ft" in html
    assert "variable direction" in html and "visibility 0.25 miles" in html
    assert 'class="report LIFR"' in html

def test_route_calm_wind():
    html = page("KHIO", CALM)
    assert "calm wind" in html and "<dd>calm</dd>" in html

def test_route_no_code_skips_fetch():
    with mock.patch("app.fetch_metar") as fetch:
        html = app.test_client().get("/").get_data(as_text=True)
    assert not fetch.called and "report" not in html.split("</form>")[1]

def test_route_error_messages():
    assert "No METAR found" in page("ZZZZ", side_effect=MetarError("No METAR found for 'ZZZZ'."))
    assert 'role="alert"' in page("ZZZZ", side_effect=MetarError("bad"))
    assert "reach the weather service" in page("KJFK", side_effect=requests.ConnectionError())
    assert "Something went wrong" in page("KJFK", {"icaoId": "KJFK"})   # rawOb missing
    assert "&lt;b&gt;" in page("<b>", side_effect=MetarError("'<b>' is invalid"))   # escaped


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
    print(f"all tests passed ({len(tests)})")
