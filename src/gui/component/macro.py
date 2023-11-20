from pathlib import Path
from tkinter import StringVar, Tk, filedialog, ttk

from ..measure import Measure


class Macro(ttk.Frame):
    def __init__(self, master: Tk, meas: Measure) -> None:
        super().__init__(master)

        title = ttk.Label(self, text="Macro")
        title.pack(anchor="w")

        # Macro file entry
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        path = StringVar()
        path_entry = ttk.Entry(frame, textvariable=path, width=70)
        path_entry.pack(side="left")

        def browse_file():
            _path = filedialog.askopenfilename(
                filetypes=[("pythonファイル", "*.py *.ssr")],
                title="マクロを選択してください",
                initialdir=meas.macrodir,
            )
            path.set(_path)
            meas.set_macro_path(Path(_path))

        browse = ttk.Button(
            frame,
            text="参照",
            state="disabled",
            command=browse_file,
        )
        browse.pack(side="left")

        def toggle_button_state(meas):
            if meas.macrodir is not None:
                browse["state"] = "normal"
            else:
                browse["state"] = "disabled"

        meas.add_config_callback(toggle_button_state)
