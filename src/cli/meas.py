import os
import sys
import time
import typing as t

# hack
import measurement_manager as mm
import win32api
import win32con

# hack
from variables import USER_VARIABLES

from scripts.define import read_deffile
from scripts.log import set_user_log
from scripts.macro import get_macro, get_macropath
from scripts.macro_grammar import macro_grammer_check


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
    read_deffile()

    # ユーザー側にlogファイル表示
    set_user_log(USER_VARIABLES.TEMPDIR)

    # マクロファイルのパスを取得
    macropath, _, macrodir = get_macropath()

    # scriptsフォルダーを検索パスに追加
    # これがなくても動くっぽいけどわかりやすさのために記述
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # カレントディレクトリを測定マクロ側に変更
    os.chdir(str(macrodir))

    # マクロファイルをマクロに変換
    macro = get_macro(macropath)

    # マクロがSSRの文法規則を満たしているかチェック
    macro_grammer_check(macro)

    # 強制終了時の処理を追加
    on_forced_termination(lambda: mm.finish())

    # 測定開始
    mm.start_macro(macro)


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
