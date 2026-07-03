from metar import decode, decode_wx_string, compass_point, c_to_f

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

if __name__ == "__main__":
    test_decode_clear()
    test_decode_rain_gust()
    test_compass_and_temp()
    test_wx_string_thunderstorm()
    print("all tests passed")
