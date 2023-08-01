import ctypes
import sys
from logging import getLogger

from rich.prompt import Prompt

from measure.variable import init as init_var

from .log import init_log
from .meas import meas
from .recalculate import recalculate
from .split import split

logger = getLogger(__name__)

MODE = ["MEAS", "SPLIT", "RECALCULATE"]


def init_win() -> None:
    """変数のセット"""

    # 簡易編集モードをOFFにするためのおまじない
    # (簡易編集モードがONだと、画面をクリックしたときに処理が停止してしまう)
    kernel32 = ctypes.windll.kernel32
    # 簡易編集モードとENABLE_WINDOW_INPUTとENABLE_VIRTUAL_TERMINAL_INPUTをOFFに
    mode = 0xFDB7
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)


def main() -> None:
    mode = ""
    if len(sys.argv) > 1:
        # devフラグがあったらログレベルをDEBUGにする
        try:
            sys.argv.pop(sys.argv.index("--dev"))
            dev = True
        except ValueError:
            dev = False
        mode = sys.argv[1].upper()
    if not mode in MODE:
        mode = Prompt.ask(
            "Mode is",
            choices=["MEAS", "SPLIT", "RECALCULATE"],
            default="MEAS",
        )

    try:
        init_win()
        init_var()
        init_log(dev)

        match mode:
            case "MEAS":
                meas()
            case "SPLIT":
                split()
            case "RECALCULATE":
                recalculate()
    except Exception as e:
        logger.exception(e)
