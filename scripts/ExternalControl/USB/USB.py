"""
USB通信周りの処理はUSBと同じ書き方でできそうなので流用
うまくいかないケースがあったらその時書き換えてください
"""
from logging import getLogger
from typing import Union

import pyvisa
from utility import MyException

logger = getLogger(__name__)


class USBError(MyException):
    """USB関係のえらー"""


class USBController:
    """
    USB機器に接続するクラス
    """

    _instrument = None

    def connect(self, address: str):
        """
        指定されたUSBアドレスに接続(種類は調べない. 何かつながっていればOK)

        Parameters
        _________

        address: string or int
            機器のUSBアドレス (NIMAXで確認できる. 逆にNIMAXで確認できないものは少なくともこのコードでは接続できない)

        Returns
        _________

        inst :型不明
            機器にアクセスできるインスタンス

        """

        
        if type(address) is not str:
            raise USBError("USBController.connectの引数はstrでなければなりません")

        try:
            resource_manager = pyvisa.ResourceManager()
        except ValueError as e:
            raise USBError("VISAがPCにインストールされていない可能性があります。 NIVISAをインストールしてください") from e
        except Exception as e:  # エラーの種類に応じて場合分け
            raise USBError("予期せぬエラーが発生しました") from e

        try:
            # 機器にアクセス. USBがつながってないとここでエラーが出る
            inst = resource_manager.open_resource(address)
        except pyvisa.errors.VisaIOError as e:  # エラーが出たらここを実行
            raise USBError("USBケーブルが抜けている可能性があります") from e
        except Exception as e:  # エラーの種類に応じて場合分け
            raise USBError("予期せぬエラーが発生しました") from e

        try:
            # IDNコマンドで機器と通信. USB番号に機器がないとここでエラー
            inst.query("*IDN?")
        except pyvisa.errors.VisaIOError as e:
            raise USBError(
                address + "が'IDN?'コマンドに応答しません. 入力したUSBポートの番号が間違っている可能性があります\nUSBポートの番号はNIMAXから確認してください"
            ) from e
        except Exception as e:
            raise USBError("予期せぬエラーが発生しました") from e

        # 問題が無ければinstrumentにいれる
        self._instrument = inst

    def write(self, command):
        """
        機器に書き込み
        """
        if self._instrument is None:
            raise USBError("write()を呼ぶより前に機器に接続してください")
        self._instrument.write(command)

    def read(self):
        """
        読み取り
        """
        if self._instrument is None:
            raise USBError("read()を呼ぶより前に機器に接続してください")
        self._instrument.read()

    def query(self, command):
        """
        機器に書き込みして読み取り
        """
        if self._instrument is None:
            raise USBError("query()を呼ぶより前に機器に接続してください")
        return self._instrument.query(command)
