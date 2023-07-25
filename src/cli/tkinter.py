import tkinter.filedialog as tkfd
from pathlib import Path
from tkinter import Tk


def ask_open_filename(filetypes=None, title=None, initialdir=None, initialfile=None):
    """ファイル選択ダイアログをつくってファイルを返す関数"""
    tk = Tk()

    # ファイルダイアログでファイルを取得
    path = tkfd.askopenfilename(
        filetypes=filetypes,
        title=title,
        initialdir=initialdir,
        initialfile=initialfile,
    )

    # これとtk=Tk()がないと謎のウィンドウが残って邪魔になる
    tk.destroy()

    return Path(path).absolute()


def ask_save_filename(
    filetypes=None, title=None, initialdir=None, initialfile=None, defaultextension=None
):
    """ファイル選択ダイアログをつくってファイルを返す関数"""
    tk = Tk()

    # ファイルダイアログでファイルを取得
    path = tkfd.asksaveasfilename(
        filetypes=filetypes,
        title=title,
        initialdir=initialdir,
        initialfile=initialfile,
        defaultextension=defaultextension,
    )

    # これとtk=Tk()がないと謎のウィンドウが残って邪魔になる
    tk.destroy()

    return Path(path).absolute()
