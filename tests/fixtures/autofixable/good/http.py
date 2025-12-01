import requests

def get_data():
    response = requests.get("https://example.com")
    payload = response.json()
    return payload
