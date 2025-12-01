import requests

def get_data():
    result = requests.get("https://example.com")
    data = result.json()
    return data
