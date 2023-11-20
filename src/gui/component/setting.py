from logging import getLogger
from pathlib import Path
from tkinter import StringVar, Tk, filedialog, ttk

from ..measure import Measure

logger = getLogger(__name__)


class Setting(ttk.Frame):
    def __init__(self, master: Tk, meas: Measure) -> None:
        super().__init__(master)

        title = ttk.Label(self, text="Setting")
        title.pack(anchor="w")

        # Setting file entry
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        path = StringVar()
        path_entry = ttk.Entry(frame, textvariable=path, width=70)
        path_entry.pack(side="left")

        def browse_file():
            _path = filedialog.askopenfilename(
                filetypes=[("設定ファイル", "*.def")],
                title="設定ファイルを選んでください",
            )
            path.set(_path)

        def load_setting():
            _path = path.get()
            if _path != "":
                try:
                    meas.set_settings(Path(_path))

                except Exception as e:
                    logger.exception(e)
                    return

                datadir.set(f"DATADIR = {meas.datadir}")
                tmpdir.set(f"TMPDIR = {meas.tmpdir}")
                macrodir.set(f"MACRODIR = {meas.macrodir}")

        browse = ttk.Button(frame, text="参照", command=browse_file)
        browse.pack(side="left")

        load = ttk.Button(frame, text="読み込み", command=load_setting)
        load.pack(side="left")

        # Loaded data
        data_frame = ttk.Frame(self)
        data_frame.pack(fill="both", expand=True)

        datadir = StringVar(value="DATADIR = ")
        data_dir = ttk.Label(data_frame, textvariable=datadir)
        data_dir.pack(anchor="w")
        tmpdir = StringVar(value="TMPDIR = ")
        tmp_dir = ttk.Label(data_frame, textvariable=tmpdir)
        tmp_dir.pack(anchor="w")
        macrodir = StringVar(value="MACRODIR = ")
        macro_dir = ttk.Label(data_frame, textvariable=macrodir)
        macro_dir.pack(anchor="w")
