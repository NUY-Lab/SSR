"""
measurement_managerモジュールで利用するクラスの詰め合わせ
"""


import msvcrt
import threading
import time
from logging import getLogger

logger = getLogger(__name__)


# コマンドの入力を受け取るクラス
class CommandReceiver:
    """コマンドの入力を検知する

    Attributes
    ----------

    __comand: str | None
        入力されたコマンド
        スレッド間で共有する
        コマンド入力がないときはNone
    __isfinish: bool
        測定の終了
    """

    __command: str | None = None
    __measurement_state = None

    def __init__(self, measurement_state: MeasurementState) -> None:
        self.__measurement_state = measurement_state

    def initialize(self) -> None:
        """別スレッドで__command_receive_threadを実行"""
        cmthr = threading.Thread(target=self.__command_receive_thread)
        cmthr.setDaemon(True)
        cmthr.start()

    # 終了コマンドの入力待ち, これは別スレッドで動かす
    def __command_receive_thread(self) -> None:
        while True:
            # 入力が入って初めてinputが動くように(inputが動くとその間ループを抜けられないので)
            if msvcrt.kbhit() and self.__measurement_state.is_measuring():
                command = input()
                if command != "":
                    self.__command = command
                    logger.info("command:%s", self.__command)
                    while self.__command is not None:
                        time.sleep(0.1)
            elif self.__measurement_state.has_finished_measurement():
                break
            time.sleep(0.1)

    def get_command(self) -> str:
        """受け取ったコマンドを返す. なければNoneを返す"""
        command = self.__command
        self.__command = None
        return command
