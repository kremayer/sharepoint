"""iPhone -> folder transfer. Run: python app.py  (Windows; use --demo SRC to test with a folder)."""
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from iphone_transfer.core import transfer

# Transfers land next to the app, so everything stays in the folder you put it in.
DEFAULT_DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Transfers")


def make_backend(demo_src):
    if demo_src:
        from iphone_transfer.backend_local import LocalBackend
        return LocalBackend(demo_src)
    from iphone_transfer.backend_windows import WindowsBackend
    return WindowsBackend()


class App(tk.Tk):
    def __init__(self, demo_src=None):
        super().__init__()
        self.title("iPhone Photo & Video Transfer")
        self.geometry("640x460")
        self.demo_src = demo_src
        self.q = queue.Queue()
        self.cancel = threading.Event()
        self.dest = tk.StringVar(value=DEFAULT_DEST)
        self.delete_after = tk.BooleanVar(value=True)

        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Destination folder:").pack(side="left")
        ttk.Entry(top, textvariable=self.dest).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(top, text="Browse...", command=self.browse).pack(side="left")
        ttk.Checkbutton(self, text="Delete from iPhone after each file is copied and verified",
                        variable=self.delete_after).pack(anchor="w", padx=8)
        row = ttk.Frame(self, padding=8)
        row.pack(fill="x")
        self.start_btn = ttk.Button(row, text="Start", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(row, text="Stop", command=self.cancel.set, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        self.bar = ttk.Progressbar(row, mode="determinate")
        self.bar.pack(side="left", fill="x", expand=True, padx=6)
        self.logbox = scrolledtext.ScrolledText(self, state="disabled")
        self.logbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.after(100, self.pump)

    def browse(self):
        d = filedialog.askdirectory()
        if d:
            self.dest.set(d)

    def start(self):
        if not self.dest.get():
            messagebox.showwarning("Folder needed", "Choose a destination folder first.")
            return
        if self.delete_after.get() and not messagebox.askyesno(
                "Confirm", "Files will be DELETED from the iPhone after they are copied. Continue?"):
            return
        self.cancel.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.work, daemon=True).start()

    def work(self):
        try:
            backend = make_backend(self.demo_src)
            transfer(backend, self.dest.get(), self.delete_after.get(),
                     log=lambda m: self.q.put(("log", m)),
                     progress=lambda d, t: self.q.put(("prog", (d, t))),
                     cancel=self.cancel)
        except Exception as e:
            self.q.put(("log", f"ERROR: {e}"))
        self.q.put(("end", None))

    def pump(self):
        while not self.q.empty():
            kind, val = self.q.get()
            if kind == "log":
                self.logbox.config(state="normal")
                self.logbox.insert("end", val + "\n")
                self.logbox.see("end")
                self.logbox.config(state="disabled")
            elif kind == "prog":
                self.bar.config(maximum=val[1], value=val[0])
            else:
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
        self.after(100, self.pump)


if __name__ == "__main__":
    demo = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--demo" else None
    App(demo).mainloop()
