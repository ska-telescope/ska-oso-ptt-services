import json
import os


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
        return json_data


# json_file_path = "unit/ska_oso_slt_services/routers/test_data_files"
