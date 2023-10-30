"""
MAX-303と直接通信するクラスや入力値の検証を行うクラスが入っている
"""
import math
from enum import Enum
from logging import getLogger
from typing import Tuple

import serial
from utility import MyException

logger = getLogger(f"SSR.{__name__}")


class MAX303Error(MyException):
    """MAX-303関係のエラー"""


class MAX303SerialIO:
    """MAX-303と直接通信を担当するクラス

    Attributes
    ----------
    serial:
        serialモジュールにあるシリアル通信用のインスタンス
    """

    def connect(self, COMPORT: str) -> None:
        """シリアル接続

        Parameter
        ---------
        COMPORT:
            シリアルポートのポート番号 (COM1 or COM2 or COM3 or ...)
            デバイスマネージャーやNIMAXから確認できる
        """
        try:
            # シリアルポートに接続(COMPORT以外の設定はマニュアル参照)
            self.ser = serial.Serial(
                port=COMPORT,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                timeout=0.5,
            )
        except Exception as e:
            raise MAX303Error(
                f"{COMPORT}に繋がりません。\nデバイスマネージャーなどを調べてMAX-303の正しいCOMポート番号を'COM(数字)'の形式でMAX-303ManualContollerに入力してください"
            )

        _ = self.ser.read_all()  # 溜まっているコマンドを掃除

        # Tコマンドを送ってなにか返ってきたらOK
        ans = self.query("T")
        if len(ans) < 10:
            raise MAX303Error(
                f"{COMPORT}にTコマンドを行った結果'{ans}'が返されました。MAX-303以外の機器である可能性があります"
            )

    def write(self, command: str) -> None:
        """シリアル通信で書き込み

        Parameters
        ----------
        command:str
            コマンド
        """
        command = command + "\r\n"  # "\r"がCarriage Return, "\n"がLine Feedを追加
        self.ser.write(command.encode("utf-8"))  # バイト列に変換して送信
        _ = self.ser.read_until(b"\r\n")  # 空の応答が返ってくるので捨てる

    def query(self, command: str) -> bytes:
        """シリアル通信で書き込み&読み取り

        Parameters
        ----------
        command:str
            コマンド

        Returns
        -------
        ans : bytes
            機器からの返答をバイト列で返す
        """
        self.write(command)
        ans = self.ser.read_until(b"\r\n")  # \r\nを最後尾に含む応答が返ってくるまで待つ
        return ans
