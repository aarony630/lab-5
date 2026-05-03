"""
Component D: External API assert statements for the Open-Meteo integration.
"""
import requests


def test_open_meteo_valid_request():
    url = "https://api.open-meteo.com/v1/forecast?latitude=47.6062&longitude=-122.3321&current_weather=true"
    response = requests.get(url, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "current_weather" in data
    assert isinstance(data["current_weather"]["temperature"], (int, float))
    assert isinstance(data["current_weather"]["windspeed"], (int, float))


def test_open_meteo_invalid_latitude():
    url = "https://api.open-meteo.com/v1/forecast?latitude=999&longitude=-122.3321&current_weather=true"
    response = requests.get(url, timeout=5)
    assert response.status_code == 400


def test_open_meteo_no_auth_needed():
    url = "https://api.open-meteo.com/v1/forecast?latitude=47.6062&longitude=-122.3321&current_weather=true"
    response = requests.get(url, timeout=5)
    assert response.status_code != 401
