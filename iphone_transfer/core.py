"""Backend-independent transfer logic: copy, verify, then delete (cut and paste)."""
import os
import threading
from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Protocol


@dataclass
class RemoteFile:
    name: str
    size: int
    handle: object  # backend-specific reference


class Backend(Protocol):
    def list_files(self) -> Iterable[RemoteFile]: ...
    def fetch(self, f: RemoteFile, dest_path: str) -> None: ...
    def delete(self, f: RemoteFile) -> None: ...


@dataclass
class Summary:
    copied: int = 0
    renamed: int = 0
    deleted: int = 0
    failed: int = 0
    bytes: int = 0


def unique_path(folder: str, name: str, taken: set) -> str:
    """Return a path in folder that does not exist; IMG_1.JPG -> IMG_1_1.JPG, IMG_1_2.JPG..."""
    stem, ext = os.path.splitext(name)
    n = 0
    while True:
        candidate = name if n == 0 else f"{stem}_{n}{ext}"
        path = os.path.join(folder, candidate)
        if path.lower() not in taken and not os.path.exists(path):
            taken.add(path.lower())
            return path
        n += 1


def transfer(
    backend: Backend,
    dest: str,
    delete_after: bool = True,
    log: Callable[[str], None] = print,
    progress: Callable[[int, int], None] = lambda done, total: None,
    cancel: Optional[threading.Event] = None,
) -> Summary:
    os.makedirs(dest, exist_ok=True)
    files = list(backend.list_files())
    total = len(files)
    log(f"Found {total} files.")
    s = Summary()
    taken: set = set()
    for i, f in enumerate(files, 1):
        if cancel is not None and cancel.is_set():
            log("Stopped by user.")
            break
        final = unique_path(dest, f.name, taken)
        part = final + ".part"
        try:
            backend.fetch(f, part)
            got = os.path.getsize(part)
            if got != f.size:
                raise IOError(f"size mismatch (phone {f.size}, copy {got})")
            os.replace(part, final)
        except Exception as e:  # keep going; never delete a file that failed
            s.failed += 1
            log(f"FAILED {f.name}: {e}")
            if os.path.exists(part):
                os.remove(part)
            progress(i, total)
            continue
        s.copied += 1
        s.bytes += f.size
        if os.path.basename(final) != f.name:
            s.renamed += 1
            log(f"Copied {f.name} -> {os.path.basename(final)} (name existed)")
        else:
            log(f"Copied {f.name}")
        if delete_after:
            try:
                backend.delete(f)
                s.deleted += 1
            except Exception as e:
                s.failed += 1
                log(f"Copied but could NOT delete {f.name} from iPhone: {e}")
        progress(i, total)
    log(f"Done. Copied {s.copied}, renamed {s.renamed}, deleted {s.deleted}, failed {s.failed}.")
    return s
