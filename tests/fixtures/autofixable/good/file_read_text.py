from pathlib import Path

def read_file_content():
    file_content = Path("file.txt").read_text()
    return file_content
