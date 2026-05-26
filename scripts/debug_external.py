"""Debug script to preview the GUI in external mode with a parent window."""

import sys
import os
import tkinter as tk
from PIL import Image, ImageTk

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exe2iconset import run_icon_picker


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else None

    dnd_available = TkinterDnD is not None

    if dnd_available:
        try:
            parent = TkinterDnD.Tk()
        except Exception:
            parent = tk.Tk()
    else:
        parent = tk.Tk()

    parent.title("Parent Application (Wrapper Builder)")
    parent.geometry("500x450")

    btn = tk.Button(
        parent,
        text="Open Icon Picker",
        command=lambda: open_picker(parent, input_file),
    )
    btn.pack(pady=(10, 5))

    preview_frame = tk.LabelFrame(parent, text="Preview")
    preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    preview_label = tk.Label(preview_frame, text="No icon selected")
    preview_label.pack(expand=True)

    info_label = tk.Label(parent, text="", anchor=tk.W)
    info_label.pack(fill=tk.X, padx=10, pady=(0, 10))

    parent.preview_label = preview_label
    parent.info_label = info_label
    parent.photo_ref = None

    parent.mainloop()


def open_picker(parent, input_file):
    result = run_icon_picker(external_mode=True, input_file=input_file, parent=parent)
    if result:
        print("Selected:", result["series_key"])
        print("Icons count:", len(result["icons"]))
        icons = result["icons"]
        if icons:
            first = icons[0]
            img = first["image"]
            w, h = first.get("width", 0), first.get("height", 0)
            parent.info_label.config(
                text=f"Series: {result['series_key']}  |  First icon: {w}x{h}  |  Total: {len(icons)} icons"
            )
            max_display = 200
            if h > max_display:
                scale = max_display / h
                img = img.resize((int(w * scale), max_display), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            parent.photo_ref = photo
            parent.preview_label.config(image=photo, text="")
    else:
        print("Cancelled")
        parent.info_label.config(text="")
        parent.preview_label.config(image="", text="No icon selected")
        parent.photo_ref = None


if __name__ == "__main__":
    main()
