import os
import time
import typing as t
from logging import getLogger

import win32api
import win32con

from measure.macro import get_prev_macro_name, load_macro, save_current_macro_name
from measure.macro_grammar import macro_grammer_check
from measure.masurement import finish, start_macro
from measure.setting import (
    get_prev_setting_path,
    load_settings,
    save_current_setting_path,
)
from measure.variable import USER_VARIABLES

from .log import init_user_log
from .rich import console
from .tkinter import ask_open_filename

logger = getLogger(__name__)


def meas() -> None:
    """
    測定マクロを動かすための準備をするスクリプト

    実装としては

    定義ファイル選択
    ↓
    測定マクロ選択
    ↓
    測定マクロ読み込み
    ↓
    必要な関数(updateなど)があるか確認
    ↓
    measurementManager._measure_startを実行
    """

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
    load_settings(setting_path)

    # ユーザー側にlogファイル表示
    init_user_log(USER_VARIABLES.TEMPDIR)

    # マクロファイルのパスを取得
    prev_macro_name = get_prev_macro_name()
    with console.status("マクロ選択..."):
        macro_path = ask_open_filename(
            filetypes=[("pythonファイル", "*.py *.ssr")],
            title="マクロを選択してください",
            initialdir=USER_VARIABLES.MACRODIR,
            initialfile=prev_macro_name,
        )
    logger.info(f"Macro: {macro_path.name}")
    save_current_macro_name(macro_path.name)

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(str(macro_path.parent))

    # マクロファイルをマクロに変換
    macro = load_macro(macro_path)

    # マクロがSSRの文法規則を満たしているかチェック
    macro_grammer_check(macro)

    # 強制終了時の処理を追加
    on_forced_termination(lambda: finish())

    # 測定開始
    # with console.status("測定中"):
    start_macro(macro, console)


def on_forced_termination(func: t.Callable[[None], None]) -> None:
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

    # イベントが起きたときにconsoleCtrHandlerを実行するようにPCに命令
    win32api.SetConsoleCtrlHandler(consoleCtrHandler, True)
