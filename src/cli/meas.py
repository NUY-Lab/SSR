import os
import time
from logging import getLogger
from multiprocessing import Event, Process, Queue
from queue import Empty
from typing import Callable

import win32api
import win32con

from measure.macro import get_prev_macro_name, save_current_macro_name
from measure.measurement import Measurement
from measure.setting import (
    get_prev_setting_path,
    load_settings,
    save_current_setting_path,
)

from .log import init_user_log
from .plot import DEFAULT_INFO, PlotWindow
from .rich import console
from .tkinter import ask_open_filename

logger = getLogger(__name__)


def meas() -> None:
    # 定義ファイル読み取り
    prev_setting_path = get_prev_setting_path()
    if prev_setting_path is not None:
        setting_dir = str(prev_setting_path.parent)
        setting_name = prev_setting_path.name
    else:
        setting_dir = None
        setting_name = None
    with console.status("設定ファイル選択..."):
        setting_path = ask_open_filename(
            filetypes=[("設定ファイル", "*.def")],
            title="設定ファイルを選んでください",
            initialdir=setting_dir,
            initialfile=setting_name,
        )
    logger.info(f"Setting: {setting_path.name}")
    save_current_setting_path(setting_path)
    (datadir, tmpdir, macrodir) = load_settings(setting_path)

    # ユーザー側にlogファイル表示
    init_user_log(tmpdir)

    # マクロファイルのパスを取得
    prev_macro_name = get_prev_macro_name()
    with console.status("マクロ選択..."):
        macro_path = ask_open_filename(
            filetypes=[("pythonファイル", "*.py *.ssr")],
            title="マクロを選択してください",
            initialdir=macrodir,
            initialfile=prev_macro_name,
        )
    logger.info(f"Macro: {macro_path.name}")
    save_current_macro_name(macro_path.name)

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(str(macro_path.parent))

    # 測定開始
    q = Queue(maxsize=10)
    abort = Event()
    measurement = Measurement(datadir, macro_path, q, abort)
    p = Process(target=measurement.run)
    pw = None
    pw_info = None

    # 強制終了時の処理を追加
    on_forced_termination(lambda: abort.set())

    with console.status("測定中"):
        p.start()

        while True:
            # 測定側からのキューを処理する
            try:
                msg = q.get_nowait()

                if msg[0] == "plot":
                    (key, x, y) = msg[1]
                    if pw is None:
                        pw = PlotWindow({key: ([x], [y])}, pw_info)
                        pw.plot(DEFAULT_INFO)
                    else:
                        pw.append(key, x, y)
                    continue
                elif msg[0] == "plot:info":
                    pw_info = msg[1]
                elif msg[0] == "log":
                    console.log(msg[1])
                    continue
                elif msg[0] == "finish":
                    print("finish")
                    break
            except Empty:
                pass

            # プロットのイベントを処理する
            if pw is not None:
                if not pw.is_active():
                    abort.set()
                    pw = None
                    break
                pw.flush_events()
            time.sleep(0.033)  # 1/30 s
        p.join()

    while True:
        if not pw.is_active():
            break
        pw.flush_events()
        time.sleep(0.033)


def on_forced_termination(func: Callable[[None], None]) -> None:
    """強制終了時の処理を追加する"""

    def consoleCtrHandler(ctrlType):
        """コマンドプロンプト上でイベントが発生したときに呼ばれる関数
        PC側で実行される(こちらから実行はしない)

        Parameter
        ---------
        ctrlType:
            イベントの種類 (バツボタンクリックやcrtl + C など)
        """

        if ctrlType == win32con.CTRL_CLOSE_EVENT:
            func()
            print("terminating measurement...")
            for i in range(100):
                time.sleep(1)

        elif ctrlType == win32con.CTRL_C_EVENT or ctrlType == win32con.CTRL_BREAK_EVENT:
            func()
            print("terminating measurement...")

    # イベントが起きたときにconsoleCtrHandlerを実行するようにPCに命令
    win32api.SetConsoleCtrlHandler(consoleCtrHandler, True)
