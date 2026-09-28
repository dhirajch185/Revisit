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

if __name__ == "__main__":
    test_decode_clear()
    test_decode_rain_gust()
    test_compass_and_temp()
    test_wx_string_thunderstorm()
    test_ceiling_not_highest_layer()
    test_vicinity_and_variable_wind()
    test_facts()
    test_fetch_errors()
    print("all tests passed")
