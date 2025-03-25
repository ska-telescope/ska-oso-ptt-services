import json
import os
from datetime import datetime
from pathlib import Path

TESTFILES_PATH = "unit/ska_oso_ptt_services/routers/test_data_files"


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    print(f"***********path: {path}")
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
        return json_data
