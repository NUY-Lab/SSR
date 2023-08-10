import os
import shutil

from measure.macro import load_recalculate_macro

from .rich import console
from .tkinter import ask_open_filename


def recalculate() -> None:
    with console.status("再計算マクロ選択..."):
        macro_path = ask_open_filename(
            filetypes=[("pythonファイル", "*.py *.SSR")],
            title="再計算マクロを選択してください",
        )

    os.chdir(str(macro_path.parent))
    console.print(f"[green]✔ MACRO:[/green] {macro_path.stem}")

    macro = load_recalculate_macro(macro_path)

    with console.status("再計算ファイル選択..."):
        filepath = ask_open_filename(
            filetypes=[("データファイル", "*.txt *dat")],
            title="再計算するファイルを選択してください",
        )

    filepath = str(filepath)
    old_filepath = filepath + ".old"
    new_filepath = filepath + ".recalc"
    shutil.move(filepath, old_filepath)

    with open(old_filepath, encoding="utf-8") as old_file:
        with open(new_filepath, "x", encoding="utf-8") as new_file:
            skip_line = int(console.input("skip_line_num > "))
            for _ in range(skip_line):
                new_file.write(old_file.readline())
            for l in old_file.readlines():
                data = [float(n) for n in l.split(",")]
                new_file.write(macro.recalculate(data) + "\n")

    console.print("recalculate completed...")
