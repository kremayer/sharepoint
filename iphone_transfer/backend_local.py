"""Folder-as-phone backend, used for tests and for trying the app without a phone."""
import os
import shutil
from typing import Iterable

from .core import RemoteFile


class LocalBackend:
    def __init__(self, root: str):
        self.root = root

    def list_files(self) -> Iterable[RemoteFile]:
        for d, _, names in os.walk(self.root):
            for n in sorted(names):
                p = os.path.join(d, n)
                yield RemoteFile(n, os.path.getsize(p), p)

    def fetch(self, f: RemoteFile, dest_path: str) -> None:
        shutil.copyfile(f.handle, dest_path)

    def delete(self, f: RemoteFile) -> None:
        os.remove(f.handle)
