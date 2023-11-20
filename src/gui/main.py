from io import StringIO
from logging import getLogger
from tkinter import Tk

from .component.controller import MeasController
from .component.log import Log
from .component.macro import Macro
from .component.setting import Setting
from .log import init_log
from .measure import Measure

logger = getLogger(__name__)


def main():
    log_stream = StringIO()
    init_log(log_stream)

    logger.info("start")

    root = Tk()
    root.title("SSR")
    root.geometry("600x400")

    meas = Measure(root)

    setting = Setting(root, meas)
    setting.pack(padx=16, pady=16, fill="both", expand=True)

    macro = Macro(root, meas)
    macro.pack(padx=16, pady=16, fill="both", expand=True)

    controller = MeasController(root, meas)
    controller.pack(padx=16, pady=16, fill="both", expand=True)

    log = Log(root, log_stream)
    log.pack(padx=16, pady=16, fill="both", expand=True)

    logger.info("mainloop")
    root.mainloop()
