import requests

def get_data():
    response = "some other response"
    response_2 = requests.get("https://example.com")
    return response_2
