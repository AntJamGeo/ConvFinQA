import json       

from entry import Entry

def load_data(file_path):
    with open(file_path) as json_file:
        json_data = json.load(json_file)
    data = {}
    for k, v in json_data.items():
        data[int(k)] = Entry(
            id=int(k),
            type=v["type"],
            context=v["context"],
            questions=v["dialogue_break"],
            answers=v["answers"],
            exe_answers=v["exe_ans_list"]
        )
    return data