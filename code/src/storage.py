from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict


class JsonStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.base_dir / f"{name}.json"

    def load(self, name: str, default: Any) -> Any:
        p = self._path(name)
        if not p.exists():
            return default
        return json.loads(p.read_text(encoding="utf-8"))

    def save(self, name: str, data: Any) -> None:
        p = self._path(name)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)