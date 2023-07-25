import os

from scripts.macro import get_macro_recalculate
from scripts.recalculate import recalc

from .rich import console
from .tkinter import ask_open_filename


def recalculate() -> None:
    with console.status("再計算マクロ選択..."):
        macroPath = ask_open_filename(
            filetypes=[("pythonファイル", "*.py *.SSR")], title="再計算マクロを選択してください"
        )

    os.chdir(str(macroPath.parent))
    console.print(f"[green]✔ MACRO:[/green] {macroPath.stem}")

    target = get_macro_recalculate(macroPath)

    with console.status("再計算ファイル選択..."):
        filePath = ask_open_filename(
            filetypes=[("データファイル", "*.txt *dat")], title="再計算するファイルを選択してください"
        )

    recalc(target, filePath)
