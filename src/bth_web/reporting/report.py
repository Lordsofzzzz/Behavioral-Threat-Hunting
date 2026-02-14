import json
from typing import Iterable, Dict, Any

def write_json(path: str, data: Iterable[Dict[str, Any]]) -> None:
    out = list(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
