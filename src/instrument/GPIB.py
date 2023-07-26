"""GPIB周りの処理"""
from logging import getLogger

import pyvisa
from pyvisa.resources import GPIBInstrument

from measure.error import SSRError

logger = getLogger(__name__)


class GPIBError(SSRError):
    """GPIB関係のエラー"""


class GPIBController:
    """GPIB機器に接続するクラス"""

    _instrument: GPIBInstrument | None = None

    def connect(self, address: int | str):
        """指定されたGPIBアドレスに接続(種類は調べない. 何かつながっていればOK)

        Parameters
        ----------

        address: string | int
            機器のGPIBアドレス stringならGPIB0::9::INSTRの形式

        Returns
        -------

        inst: pyvisa.resources.GPIBInstrument
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
        except Exception as e:
            raise GPIBError("予期せぬエラーが発生しました") from e

        try:
            # 機器にアクセス. GPIBがつながってないとここでエラーが出る
            inst: GPIBInstrument = resource_manager.open_resource(address)
        except pyvisa.errors.VisaIOError as e:  # エラーが出たらここを実行
            raise GPIBError("GPIBケーブルが抜けている可能性があります") from e
        except Exception as e:
            raise GPIBError("予期せぬエラーが発生しました") from e

        try:
            # IDNコマンドで機器と通信. GPIB番号に機器がないとここでエラー
            inst.query("*IDN?")
        except pyvisa.errors.VisaIOError as e:
            raise GPIBError(
                f"{address}が'IDN?'コマンドに応答しません. 設定されているGPIBの番号が間違っている可能性があります"
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
