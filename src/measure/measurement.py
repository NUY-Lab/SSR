"""
ユーザーのマクロを受けとって動かす
ユーザーのマクロ側から呼び出せる関数などはほとんどここにあります
一部処理はmeasurement_manager_supportに切り出しています
"""
import enum
from logging import getLogger
from multiprocessing import Queue
from pathlib import Path

import pyperclip

from measure.error import SSRError
from measure.macro import load_macro

from .macro_grammar import macro_grammer_check
from .util import get_date_text

logger = getLogger(__name__)


def set_filename(name: str | None = None, prefix: str | None = None):
    """測定データのファイル名をセットする。
    この関数を呼ばない限り測定データのファイルは作成されない。

    Parameter
    ---------
    name: str | None
        ファイル名。Noneの場合は日付になる。
    prefix: "date" | None
        ファイル名の先頭に日付を付ける。
    """
    if name is None:
        name = get_date_text() + ".txt"
    if prefix == "date":
        name = f"{get_date_text()}_{name}"
    _measurement.file.path = _measurement.datadir / name
    pyperclip.copy(name)


def set_plot_info(
    line=False,
    xlog=False,
    ylog=False,
    legend=False,
    flowwidth=0,
) -> None:
    """プロット情報の入力。グラフ描画プロセスに渡す値はここで設定する.

    Parameter
    ---------

    line: bool
        プロットに線を引くかどうか。
    xlog, ylog: bool
        対数軸にするかどうか。
    legend: bool
        凡例をつけるか(凡例の名前はlabelの値)。
    flowwidth: float (>0)
        これが0より大きい値のときグラフの横軸は固定され､横にプロットが流れるようなグラフになる。
    """
    _measurement.queue.put_nowait(
        (
            "plot:info",
            {
                "line": line,
                "xlog": xlog,
                "ylog": ylog,
                "legend": legend,
                "flowwidth": flowwidth,
            },
        )
    )


def save(*data) -> None:
    """データをファイルに書き込む。
    この関数が呼ばれるごとに書き込みの反映をおこなっているので
    途中で測定が落ちてもそれまでのデータは残るようになっている。
    測定のデータは測定マクロ側で保持しておいて最後にまとめて書き込むことも可能。

    Parameter
    ---------
    data: Any
        書き込むデータ。
    """
    if _measurement.state & (State.START | State.UPDATE | State.END):
        _measurement.file.write(*data)
    else:
        logger.error("save関数はupdate関数・end関数内でしか使えません。書き込みに失敗しました。")


plot_data_flag = False


def plot(x: float, y: float, label="default") -> None:
    """データをプロットする。labelが変わると色が変わる。

    Parameter
    ---------
    x, y: float
        プロットのx, y座標。
    label: str
        プロットの識別ラベル。同じラベルは同じ色でプロットされ、線を引き設定のときは線を引く。
    """
    if _measurement.state == State.UPDATE:
        _measurement.queue.put_nowait(("plot", (label, x, y)))
    else:
        logger.warning("plot関数はupdate関数内でしか使えません")


def print(msg: str) -> None:
    _measurement.queue.put_nowait(("log", msg))


def finish() -> None:
    """測定を終了させる"""
    logger.debug("finish is called")
    _measurement.measuring = False


def _state() -> "State":
    return _measurement.state


class State(enum.Flag):
    READY = enum.auto()
    START = enum.auto()
    UPDATE = enum.auto()
    FINISH_MEASURE = enum.auto()
    END = enum.auto()
    AFTER = enum.auto()


class DataFile:
    def __init__(self) -> None:
        self.path: Path | None = None
        self.file = None
        # ファイルが開かれる前に書き込まれたものを一時的に保存しておく
        # ファイルに書き込むにはflushを呼ぶ
        self.buf = []

    def write(self, *data) -> None:
        if self.file is None:
            if self.buf is None:
                raise SSRError("閉じられたファイルに書き込もうとしています")
            else:
                self.buf.append(",".join(map(str, data)) + "\n")
                return
        self.file.write(",".join(map(str, data)) + "\n")
        self.file.flush()

    def flush(self) -> bool:
        if self.file is None:
            if len(self.buf) > 0:
                return False
            else:
                return True
        for txt in self.buf:
            self.file.write(txt)
        self.file.flush()
        self.buf = None
        return True

    def __enter__(self) -> "DataFile":
        if self.path is not None:
            self.file = self.path.open(mode="w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file is not None:
            self.file.close()
            self.file = None
        return False


class Measurement:
    def __init__(self, datadir: Path, macropath: Path, queue: Queue, abort) -> None:
        self.state = State.READY
        self.datadir = datadir
        self.macropath = macropath
        self.queue = queue
        self.abort = abort

        self.file = DataFile()

    def run(self):
        global _measurement

        # マクロがインスタンスにアクセス出来る様に
        _measurement = self

        logger.debug("load macro")
        macro = load_macro(self.macropath)
        # macro_grammer_check(macro)

        self.state = State.START
        logger.debug("measurement state: START")
        if macro.start is not None:
            macro.start()

        if self.file.path is None:
            logger.debug("measurement data don't save")

        # ファイルを開く
        with self.file:
            if not self.file.flush():
                logger.error("start関数で書き込まれたデータの保存に失敗しました。")

            logger.debug("measurement state: UPDATE")
            self.state = State.UPDATE
            self.measuring = True
            while self.measuring:
                if self.abort.is_set():
                    self.measuring = False
                if macro.update() == False:
                    logger.debug("update function return False")
                    self.measuring = False

            logger.debug("measurement state: END")
            self.state = State.END
            if macro.end is not None:
                macro.end()

        logger.debug("measurement state: AFTER")
        self.state = State.AFTER
        if self.file.path is not None:
            if macro.split is not None:
                macro.split()
            if macro.after is not None:
                macro.after(self.file.path)

        self.queue.put_nowait(("finish",))
