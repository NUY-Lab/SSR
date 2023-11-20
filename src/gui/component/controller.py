from logging import getLogger
from tkinter import Tk, ttk

from ..measure import Measure

logger = getLogger(__name__)


class MeasController(ttk.Frame):
    def __init__(self, master: Tk, meas: Measure) -> None:
        super().__init__(master)
        self.meas = meas

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        def run_meas():
            try:
                meas.run()
            except Exception as e:
                logger.exception(e)
                abort_meas()

        def abort_meas():
            try:
                meas.abort()
            except Exception as e:
                logger.exception(e)

        run = ttk.Button(
            frame,
            text="Run",
            state="disabled",
            command=run_meas,
        )
        abort = ttk.Button(
            frame,
            text="Abort",
            state="disabled",
            command=abort_meas,
        )

        run.pack(side="left")
        abort.pack(side="left")

        def toggle_button_state_config(meas: Measure):
            if meas.macro_path is not None:
                run["state"] = "normal"
            else:
                run["state"] = "disabled"
                abort["state"] = "disabled"

        def toggle_button_state_meas(_meas: Measure, state: str):
            if state == "start":
                run["state"] = "disabled"
                abort["state"] = "normal"
            elif state == "abort" or state == "finish":
                run["state"] = "normal"
                abort["state"] = "disabled"

        self.meas.add_config_callback(toggle_button_state_config)
        self.meas.add_measurement_callback(toggle_button_state_meas)
