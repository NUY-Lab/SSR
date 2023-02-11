"""GPIB周りの処理"""
from logging import getLogger
from typing import Union

import pyvisa
from utility import MyException

logger = getLogger(__name__)


class GPIBError(MyException):
    """GPIB関係のエラー"""


def get_instrument(address: Union[int, str]) -> pyvisa.resources.Resource:
    """非推奨、GPIBControllerを使ってください"""
    a = GPIBController()
    a.connect(address)
    return a._instrument


class GPIBController:
    """GPIB機器に接続するクラス"""

    _instrument = None

    def connect(self, address: Union[int, str]):
        """指定されたGPIBアドレスに接続(種類は調べない. 何かつながっていればOK)

        Parameters
        ----------

        address: string or int
            機器のGPIBアドレス stringならGPIB0::9::INSTRの形式

        Returns
        -------

        inst :型不明
            機器にアクセスできるインスタンス
        """

        if type(address) is int:
            address = f"GPIB0::{address}::INSTR"
        elif type(address) is not str:
            raise GPIBError("GPIBController.connectの引数はintかstrでなければなりません")

        try:
            resource_manager = pyvisa.ResourceManager()
        except ValueError as e:
            raise GPIBError("VISAがPCにインストールされていない可能性があります。 NIVISAをインストールしてください") from e
        except Exception as e:  # エラーの種類に応じて場合分け
            raise GPIBError("予期せぬエラーが発生しました") from e

        try:
            # 機器にアクセス. GPIBがつながってないとここでエラーが出る
            inst = resource_manager.open_resource(address)
        except pyvisa.errors.VisaIOError as e:  # エラーが出たらここを実行
            raise GPIBError("GPIBケーブルが抜けている可能性があります") from e
        except Exception as e:  # エラーの種類に応じて場合分け
            raise GPIBError("予期せぬエラーが発生しました") from e

        try:
            # IDNコマンドで機器と通信. GPIB番号に機器がないとここでエラー
            inst.query("*IDN?")
        except pyvisa.errors.VisaIOError as e:
            raise GPIBError(
                address + "が'IDN?'コマンドに応答しません. 設定されているGPIBの番号が間違っている可能性があります"
            ) from e
        except Exception as e:
            raise GPIBError("予期せぬエラーが発生しました") from e

        # 問題が無ければinstrumentにいれる
        self._instrument = inst

    def write(self, command):
        """機器に書き込み"""
        if self._instrument is None:
            raise GPIBError("write()を呼ぶより前に機器に接続してください")
        self._instrument.write(command)

    def query(self, command):
        """機器に書き込みして読み取り"""
        if self._instrument is None:
            raise GPIBError("query()を呼ぶより前に機器に接続してください")
        return self._instrument.query(command)
