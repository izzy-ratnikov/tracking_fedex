import math
import os
import json


def format_bytes(size):
    if size == 0:
        return "0 Bytes"
    size_name = ("Bytes", "KB", "MB", "GB")
    i = int(math.log(size, 1024))
    p = pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {size_name[i]}"


def load_last_checked_number():
    if os.path.exists('last_checked.json'):
        with open('last_checked.json', 'r') as f:
            return json.load(f).get("last_number", None)
    return None


def save_last_checked_number(last_number):
    with open('last_checked.json', 'w') as f:
        json.dump({"last_number": last_number}, f)
