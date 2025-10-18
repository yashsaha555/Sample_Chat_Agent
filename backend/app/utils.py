import os
from typing import List


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def list_txt_files(folder: str) -> List[str]:
    out = []
    for root, _, files in os.walk(folder):
        for nm in files:
            if nm.lower().endswith(".txt"):
                out.append(os.path.join(root, nm))
    return out
