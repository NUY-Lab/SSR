from logging import getLogger
from multiprocessing import Event, Process, Queue
from pathlib import Path
from queue import Empty
from tkinter import Tk
from typing import Callable

from measure.error import SSRError
from measure.measurement import Measurement
from measure.setting import load_settings

from .component.plot import Plot

logger = getLogger(__name__)


class Measure:
    def __init__(self, app: Tk):
        self.app = app
        self.datadir = None
        self.tmpdir = None
        self.macrodir = None
        self.macro_path = None

        self._config_callback: list[Callable[["Measure"], None]] = []
        self._measurement_callback: list[Callable[["Measure", str], None]] = []
        self._pw = None
        self._pw_info = None

        self.p = None

    def set_settings(self, path: Path):
        (datadir, tmpdir, macrodir) = load_settings(path)
        self.datadir = datadir
        self.tmpdir = tmpdir
        self.macrodir = macrodir
        logger.info(f"Setting: {path.name}")
        for cb in self._config_callback:
            cb(self)

    def set_macro_path(self, path: Path):
        self.macro_path = path
        logger.info(f"Macro: {path.name}")
        for cb in self._config_callback:
            cb(self)

    def add_config_callback(self, cb: Callable[["Measure"], None]):
        self._config_callback.append(cb)

    def run(self):
        if self.is_alive():
            raise SSRError("測定中です")
        if self.datadir is None:
            raise SSRError("設定ファイルが読み込まれていません")
        if self.macro_path is None:
            raise SSRError("マクロファイルのパスが不明です")

        self.q = Queue(maxsize=10)
        self.e = Event()
        self.meas = Measurement(self.datadir, self.macro_path, self.q, self.e)
        self.p = Process(target=self.meas.run)

        self.app.protocol("WM_DELETE_WINDOW", self._delete_window_handler)

        self.p.start()

        self.app.after_idle(self._handler)

        for cb in self._measurement_callback:
            cb(self, "start")

    def abort(self):
        if self.is_alive():
            self.e.set()
            self.p.join()
            self._clean()
            for cb in self._measurement_callback:
                cb(self, "abort")

    def is_alive(self):
        return self.p is not None and self.p.is_alive

    def add_measurement_callback(self, cb: Callable[["Measure", str], None]):
        self._measurement_callback.append(cb)

    def _handler(self):
        if not self.is_alive():
            return

        msg = ()
        try:
            msg = self.q.get_nowait()
        except Empty:
            self._set_handler()
            return
        except Exception as e:
            logger.exception(e)
            self.abort()
            return

        if msg[0] == "plot":
            (key, x, y) = msg[1]
            try:
                if self._pw is None:
                    self._pw = Plot(self.app, {key: ([x], [y])}, self._pw_info)
                else:
                    self._pw.append(key, x, y)
            except Exception as e:
                logger.exception(e)
        elif msg[0] == "plot:info":
            self._pw_info = msg[1]
        elif msg[0] == "log":
            logger.info(msg[1])
        elif msg[0] == "finish":
            self.p.join()
            logger.info("finish")
            self._clean()
            for cb in self._measurement_callback:
                cb(self, "finish")

        self._set_handler()

    def _delete_window_handler(self):
        if self.is_alive():
            self.abort()
        self.app.destroy()

    def _clean(self):
        self.p = None
        self._pw = None
        self._pw_info = None

    def _set_handler(self):
        # https://teratail.com/questions/300512
        #   処理の流れ (※説明の為に簡略化したもので、実際の実装とは異なります)
        #   通常のイベント処理 → アイドル中のイベント処理 → 描画更新等他の処理 →
        self.app.after(0, self.app.after_idle, self._handler)
