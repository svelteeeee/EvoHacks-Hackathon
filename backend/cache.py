"""Versioned, atomic disk cache; failures and expired entries are never cache hits."""

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from backend.config import settings


def cache_key(*parts: str) -> str:
    normalized = [" ".join(p.lower().split()) for p in parts]
    return hashlib.sha256(json.dumps(["v1", *normalized]).encode()).hexdigest()


class DiskCache:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or settings.cache_dir
        self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, ttl: int | None = 3600):
        try:
            payload = json.loads((self.directory / f"{key}.json").read_text())
            if ttl is not None and time.time() - payload["timestamp"] > ttl:
                return None
            return payload["value"]
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def put(self, key: str, value) -> None:
        fd, name = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as file:
                json.dump({"timestamp": time.time(), "value": value}, file, ensure_ascii=False)
            os.replace(name, self.directory / f"{key}.json")
        finally:
            if os.path.exists(name):
                os.unlink(name)
