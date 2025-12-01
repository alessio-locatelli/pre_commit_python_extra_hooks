from pathlib import Path

def read_file_content():
    data = Path("file.txt").read_text()
    return data
