import logging
import os

from measure.macro import load_split_macro
from scripts.macro import get_macro_split

from .rich import console
from .tkinter import ask_open_filename

logger = logging.getLogger(__name__)


# 分割関数だけを呼び出し
def split() -> None:
    with console.status("分割マクロ選択"):
        macro_path = ask_open_filename(
            filetypes=[("pythonファイル", "*.py *.SSR")], title="分割マクロを選択してください"
        )

    os.chdir(macro_path.parent)
    console.print(f"[green]✔ MACRO:[/green] {macro_path.stem}")

    try:
        import scripts.ExternalControl.GPIB.GPIB as GPIB

        # GPIBモジュールの関数を書き換えてGPIBがつながって無くてもエラーが出ないようにする
        GPIB.get_instrument = lambda address: None
        logger.info("you can't use GPIB.get_instrument in GPyM_bunkatsu")
        logger.info(
            "you can't use most of measurementManager's methods in GPyM_bunkatsu"
        )
    except Exception:
        pass

    target = load_split_macro(macro_path)

    with console.status("分割ファイル選択..."):
        filePath = ask_open_filename(
            filetypes=[("データファイル", "*.txt *dat")], title="分割するファイルを選択してください"
        )

    target.split(filePath)
