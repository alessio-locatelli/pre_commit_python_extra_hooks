import json

def read_config():
    file_handle = open("config.json")
    parsed_data = json.load(file_handle)
    return parsed_data
