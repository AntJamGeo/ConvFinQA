import json       

def load_data(file_path):
    with open(file_path) as json_file:
        data = json.load(json_file)
    return {entry["index"]: entry for entry in data}