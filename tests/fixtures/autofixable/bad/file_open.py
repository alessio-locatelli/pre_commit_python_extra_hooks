import json

def read_config():
    data = open("config.json")
    result = json.load(data)
    return result
