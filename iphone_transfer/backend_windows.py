"""Windows backend: reads the iPhone through the Explorer shell (Shell.Application).

Needs pywin32. The iPhone must be unlocked, connected by USB, and "Trust" accepted.
It walks the folder tree in code, so you never have to open each folder by hand.
"""
import os
import shutil
import tempfile
import time
from typing import Iterable

import pythoncom
import win32com.client

from .core import RemoteFile

ME_FLAGS = 4 | 16 | 512 | 1024  # no progress UI, yes-to-all, no confirm, no error UI
SSF_DRIVES = 17  # "This PC"


def find_iphones():
    shell = win32com.client.Dynamic.Dispatch("Shell.Application")
    return [i for i in shell.NameSpace(SSF_DRIVES).Items() if i.IsFolder and "iphone" in i.Name.lower()]


def _real_name(item) -> str:
    # Path ends with the real file name incl. extension (Name may hide it).
    base = os.path.basename(str(item.Path).replace("/", "\\").split("\\")[-1])
    return base or item.Name


class WindowsBackend:
    def __init__(self):
        pythoncom.CoInitialize()
        self.shell = win32com.client.Dynamic.Dispatch("Shell.Application")
        self.stage = tempfile.mkdtemp(prefix="iphone_stage_")

    def _dcim(self):
        phones = find_iphones()
        if not phones:
            raise RuntimeError("No iPhone found. Unlock it, connect USB, tap Trust.")
        storage = phones[0].GetFolder.Items()
        for st in storage:  # "Internal Storage"
            for sub in st.GetFolder.Items():
                if sub.Name.upper() == "DCIM":
                    return sub.GetFolder
        raise RuntimeError("DCIM folder not found on the iPhone.")

    def list_files(self) -> Iterable[RemoteFile]:
        def walk(folder):
            for item in folder.Items():
                if item.IsFolder:
                    yield from walk(item.GetFolder)
                else:
                    yield RemoteFile(_real_name(item), int(item.Size), (folder, item))

        yield from walk(self._dcim())

    def fetch(self, f: RemoteFile, dest_path: str) -> None:
        _, item = f.handle
        staged = os.path.join(self.stage, f.name)
        if os.path.exists(staged):
            os.remove(staged)
        self.shell.NameSpace(self.stage).CopyHere(item, ME_FLAGS)
        # CopyHere is asynchronous: wait until the file is complete and stable.
        deadline = time.time() + 600
        last = -1
        while time.time() < deadline:
            if os.path.exists(staged):
                size = os.path.getsize(staged)
                if size == f.size and size == last:
                    break
                last = size
            time.sleep(0.3)
        else:
            raise TimeoutError("copy from iPhone timed out")
        shutil.move(staged, dest_path)

    def delete(self, f: RemoteFile) -> None:
        _, item = f.handle
        for verb in item.Verbs():
            if verb.Name.replace("&", "").lower().startswith("delete"):
                verb.DoIt()
                return
        raise RuntimeError("no delete verb available for this file")
