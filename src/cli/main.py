import ctypes
import sys
from pathlib import Path

# hack
import variables as variables
from rich.console import Console
from rich.prompt import Prompt

from scripts.log import setlog

from .meas import meas
from .recalculate import recalculate
from .split import split

console = Console(stderr=True)
MODE = ["MEAS", "SPLIT", "RECALCULATE"]


def init() -> None:
    """変数のセット"""
    variables.init(Path.cwd())

    # 簡易編集モードをOFFにするためのおまじない
    # (簡易編集モードがONだと、画面をクリックしたときに処理が停止してしまう)
    kernel32 = ctypes.windll.kernel32
    # 簡易編集モードとENABLE_WINDOW_INPUT と ENABLE_VIRTUAL_TERMINAL_INPUT をOFFに
    mode = 0xFDB7
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), mode)

    setlog()


def main() -> None:
    mode = ""
    if len(sys.argv) > 1:
        mode = sys.argv[1].upper()
    if not mode in MODE:
        mode = Prompt.ask(
            "Mode is", choices=["MEAS", "SPLIT", "RECALCULATE"], default="MEAS"
        )

    try:
        init()

        match mode:
            case "MEAS":
                meas()
            case "SPLIT":
                split()
            case "RECALCULATE":
                recalculate()
    except Exception as e:
        console.print_exception()
