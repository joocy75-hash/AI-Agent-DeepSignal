import requests

BASE_URL = "http://localhost:8000"

def test_health_check_endpoint_returns_system_status():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        assert response.status_code == 200
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_health_check_endpoint_returns_system_status()