"""Conservative prepublication path check; this is NOT a full secret scan."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    "datasets", "holdouts", "private", "secrets", "credentials",
    "models", "logs", "artifacts", "handoff",
}
FORBIDDEN_NAMES = {
    ".env", "credentials.json", "secret.json", "secrets.json", "id_rsa", "id_ed25519",
}
FORBIDDEN_SUFFIXES = (".zip", ".bundle", ".gguf", ".onnx", ".safetensors", ".bin", ".pem", ".key", ".p12", ".pfx", ".pt", ".pth", ".sqlite", ".db")
MAX_BYTES = 256 * 1024
# Local Git metadata and generated Python caches are not publication payload.
LOCAL_IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}


def check(root: pathlib.Path = ROOT) -> list[str]:
    bad: list[str] = []
    for item in root.rglob("*"):
        rel = item.relative_to(root)
        if any(part.lower() in LOCAL_IGNORED_PARTS for part in rel.parts):
            continue
        if (any(part.lower() in FORBIDDEN_PARTS for part in rel.parts)
                or item.name.lower() in FORBIDDEN_NAMES):
            bad.append(f"forbidden path: {rel.as_posix()}")
            continue
        if item.is_symlink():
            bad.append(f"symlink: {rel.as_posix()}")
            continue
        if item.is_file() and (item.name.lower().endswith(FORBIDDEN_SUFFIXES)
                               or item.stat().st_size > MAX_BYTES):
            bad.append(f"forbidden extension or oversize: {rel.as_posix()}")
    return sorted(set(bad))


if __name__ == "__main__":
    problems = check()
    if problems:
        for item in problems:
            print("STOP:", item)
        sys.exit(1)
    print("PUBLIC_TREE_PATH_CHECK_PASS (not a secrets/ownership audit)")
