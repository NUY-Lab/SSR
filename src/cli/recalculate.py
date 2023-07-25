import os

from measure.macro import load_recalculate_macro
from scripts.recalculate import recalc

from .rich import console
from .tkinter import ask_open_filename


def recalculate() -> None:
    with console.status("再計算マクロ選択..."):
        macro_path = ask_open_filename(
            filetypes=[("pythonファイル", "*.py *.SSR")], title="再計算マクロを選択してください"
        )

    os.chdir(str(macro_path.parent))
    console.print(f"[green]✔ MACRO:[/green] {macro_path.stem}")

    target = load_recalculate_macro(macro_path)

    with console.status("再計算ファイル選択..."):
        filePath = ask_open_filename(
            filetypes=[("データファイル", "*.txt *dat")], title="再計算するファイルを選択してください"
        )

    recalc(target, filePath)
