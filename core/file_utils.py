import os
from typing import Optional

def get_latest_file(directory: str, extensions=(".pdf", ".txt")) -> Optional[str]:
    files = [os.path.join(directory, f) for f in os.listdir(directory)
             if f.lower().endswith(extensions) and os.path.isfile(os.path.join(directory, f))]
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return latest
