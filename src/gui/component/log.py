from io import StringIO
from tkinter import Scrollbar, Text, Tk, ttk

DELAY = 1000


class Log(ttk.Frame):
    def __init__(self, master: Tk, log_stream: StringIO) -> None:
        super().__init__(master)

        title = ttk.Label(self, text="Log")
        title.pack(anchor="w")
        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")

        text = Text(
            self,
            wrap="word",
            yscrollcommand=scrollbar.set,
            state="disabled",
        )
        text.pack(fill="both", expand=True)

        def update() -> None:
            _text = log_stream.getvalue()
            log_stream.truncate(0)
            log_stream.seek(0)
            if _text != "":
                for t in _text.split("\n"):
                    text.configure(state="normal")
                    text.insert("end", t + "\n")
                    text.configure(state="disabled")
            text.yview_moveto(1.0)
            self.after(DELAY, update)

        update()
