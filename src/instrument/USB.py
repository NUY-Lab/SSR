"""
USB通信周りの処理はUSBと同じ書き方でできそうなので流用
うまくいかないケースがあったらその時書き換えてください
"""
from logging import getLogger

import pyvisa
from pyvisa.resources import USBInstrument

from measure.error import SSRError

logger = getLogger(__name__)


class USBError(SSRError):
    """USB関係のエラー"""


class USBController:
    """USB機器に接続するクラス"""

    _instrument: USBInstrument = None

    def connect(self, address: str):
        """指定されたUSBアドレスに接続(種類は調べない. 何かつながっていればOK)

        Parameters
        ----------

        address: string | int
            機器のUSBアドレス (NIMAXで確認できる. 逆にNIMAXで確認できないものは少なくともこのコードでは接続できない)

        Returns
        -------

        inst: pyvisa.resources.USBInstrument
            機器にアクセスできるインスタンス
        """

        if type(address) is not str:
            raise USBError("USBController.connectの引数はstrでなければなりません")

        try:
            resource_manager = pyvisa.ResourceManager()
        except ValueError as e:
            raise USBError("VISAがPCにインストールされていない可能性があります。 NIVISAをインストールしてください") from e
        except Exception as e:
            raise USBError("予期せぬエラーが発生しました") from e

        try:
            # 機器にアクセス. USBがつながってないとここでエラーが出る
            inst: USBInstrument = resource_manager.open_resource(address)
        except pyvisa.errors.VisaIOError as e:
            raise USBError("USBケーブルが抜けている可能性があります") from e
        except Exception as e:
            raise USBError("予期せぬエラーが発生しました") from e

        try:
            # IDNコマンドで機器と通信. USB番号に機器がないとここでエラー
            inst.query("*IDN?")
        except pyvisa.errors.VisaIOError as e:
            raise USBError(
                f"{address}が'IDN?'コマンドに応答しません."
                "入力したUSBポートの番号が間違っている可能性があります\n"
                "USBポートの番号はNIMAXから確認してください"
            ) from e
        except Exception as e:
            raise USBError("予期せぬエラーが発生しました") from e

        # 問題が無ければinstrumentにいれる
        self._instrument = inst

    def write(self, command):
        """機器に書き込み"""
        if self._instrument is None:
            raise USBError("write()を呼ぶより前に機器に接続してください")
        self._instrument.write(command)

    def read(self):
        """読み取り"""
        if self._instrument is None:
            raise USBError("read()を呼ぶより前に機器に接続してください")
        self._instrument.read()

    def query(self, command):
        """機器に書き込みして読み取り"""
        if self._instrument is None:
            raise USBError("query()を呼ぶより前に機器に接続してください")
        return self._instrument.query(command)
