"""
LinkamT95と直接通信するクラスや入力値の検証を行うクラスが入っている
"""
import math
from enum import Enum
from logging import getLogger

import serial
from serial import Serial

from measure.error import SSRError

logger = getLogger(__name__)


class LinkamT95Error(SSRError):
    """LinkamT95関係のエラー"""


class LinkamT95SerialIO:
    """LinkamT95と直接通信を担当するクラス

    Attributes
    ----------
    serial:
        serialモジュールにあるシリアル通信用のインスタンス
    """

    serial: Serial = None

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
                COMPORT,
                baudrate=19200,
                bytesize=serial.EIGHTBITS,
                stopbit=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=0.5,
            )
        except Exception as e:
            raise LinkamT95Error(
                f"{COMPORT}に繋がりません。\n"
                "デバイスマネージャーなどを調べてLinkamの正しいCOMポート番号を"
                "'COM(数字)'の形式でLinkamT95ManualContollerに入力してください"
            )

        # 溜まっているコマンドを掃除
        _ = self.ser.read_all()

        # Tコマンドを送ってなにか返ってきたらOK
        ans = self.query("T")
        if len(ans) < 10:
            raise LinkamT95Error(
                f"{COMPORT}にTコマンドを行った結果'{ans}'が返されました。LinkamT95以外の機器である可能性があります"
            )

    def write(self, command: str) -> None:
        """シリアル通信で書き込み

        Parameters
        ----------
        command: str
            コマンド
        """
        # Carriage Returnを追加
        command = command + "\r"
        # バイト列に変換して送信
        self.ser.write(command.encode("utf-8"))
        # 空の応答が返ってくるので捨てる
        _ = self.ser.read_until(b"\r")

    def query(self, command: str) -> bytes:
        """シリアル通信で書き込み&読み取り

        Parameters
        ----------
        command: str
            コマンド

        Returns
        -------
        ans: bytes
            機器からの返答をバイト列で返す
        """
        self.write(command)
        # \rを最後尾に含む応答が返ってくるまで待つ
        ans = self.ser.read_until(b"\r")
        return ans


class LinkamT95IO:
    """外からLinkamT95を動かすために用意したクラス

    主に入力値のvalidationを担当
    外のクラスからは具体的な入力コマンドを隠して関数だけを見せている

    Attributes
    ----------
    T95serial:
        LinkamT95と直接通信を行っているクラス
    """

    class State(Enum):  # 測定状態を表すenum
        Stopped = 1  # 停止中
        Heating = 2  # 昇温
        Cooling = 3  # 降温
        Holding_at_limit = 4  # 目的温度に到達してその温度を維持
        Holding_limit_time = 5  # 目的温度においてHolding
        Holding_current_temperature = 6  # 目的温度以外でHolding

    T95serial = LinkamT95SerialIO()

    def connect(self, COMPORT: str) -> None:
        """機器に接続

        Parameters
        ----------
        COMPORT:
            機器のシリアルポート番号
        """
        self.T95serial.connect(COMPORT)

    def set_limit_temperature(self, T: int) -> None:
        """目的温度設定

        Parameters
        ----------
        T:int
            目的温度
        """
        T = int(T)
        if T >= -196 and T <= 600:
            self.T95serial.write(f"L1{T}0")
        else:
            raise LinkamT95Error("設定温度は-196~600℃にしてください")

    def set_rate(self, temp_per_min: int) -> None:
        """昇温降温速度設定

        Parameters
        ----------
        temp_per_min: int
            1分間に何度変化させるか
        """
        temp_per_min = int(temp_per_min)
        if temp_per_min >= 0 and temp_per_min <= 150:
            self.T95serial.write(f"R1{temp_per_min}00")
        else:
            raise LinkamT95Error("昇温・降温速度は0~150℃にしてください")

    def set_lnp_speed(self, lnp_speed: int) -> None:
        """窒素ガス速度設定

        Parameters
        ----------
        lnp_speed: int
            ガス速度(0～100で設定)(autoは-1)
            (注)シリアル通信でのガス速度入力はタッチパッドと違って0～30での30段階入力のため、
                0~100の引数を100で割ってから30をかけて端数繰り上げして送信している
        """
        lnp_speed = int(lnp_speed)
        if lnp_speed < 0:
            self.T95serial.write("Pa0")
        elif lnp_speed <= 100:
            self.T95serial.write("Pm0")
            # T95のLNP入力が0～30 の31段階になっていて、
            # 入力するには{"0"の文字コード+LNP入力}の文字コードを入力する必要がある(0,1,2,...,9,A,B,...M,N)
            lnp_speed = math.ceil((lnp_speed / 100.0 * 30))
            # 数字を文字コードとして文字へ変換
            lnp_char = chr(lnp_speed + ord("0"))
            self.T95serial.write(f"P{lnp_char}")
        else:
            raise LinkamT95Error("lnp_speedにわたす値は100以下である必要があります")

    def start(self) -> None:
        """温度変化スタート"""
        self.T95serial.write("S")

    def stop(self) -> None:
        """停止"""
        self.T95serial.write("E")

    def heat(self) -> None:
        """昇温"""
        self.T95serial.write("H")

    def cool(self) -> None:
        """降温"""
        self.T95serial.write("C")

    def hold(self) -> None:
        """温度キープ"""
        self.T95serial.write("H")

    def read_status(self) -> tuple[State, float, int]:
        """LinkamT95に信号を送信し、返り値として測定状態の情報を受け取る

        Returns
        -------
        tuple[State,float,int]
            (実行状態(詳しくはStateを参照), 温度, 窒素ガス速度(0~100))
        """
        ans = self.T95serial.query("T")
        # ansの型はbytesだが1要素のans[0]の型はint,部分配列のans[6:10]の型はbytes(分かりづらい)
        # 測定状態(State)取得
        state = self._read_statusbyte(ans[0])
        self._check_Error(ans[1])  # エラーチェック
        pump_speed = self._read_pump_statusbyte(ans[2])
        # 温度取得(10倍された値が入っているので10分の1に)
        temperature = int.from_bytes(ans[6:10], "big", signed=True) / 10.0

        return state, temperature, pump_speed

    def _read_statusbyte(self, bytedata: bytes) -> State:
        """バイト列から測定状態を読み取る

        Parameter
        ---------
        bytedata:
            測定状態を含むbyte型のデータ

        Returns
        -------
            実行状態(昇温or降温or維持など)
        """
        # 詳しくはマニュアル参照
        stringdata = hex(bytedata)
        if stringdata == "0x1":
            state = self.State.Stopped
        elif stringdata == "0x10":
            state = self.State.Heating
        elif stringdata == "0x20":
            state = self.State.Cooling
        elif stringdata == "0x30":
            state = self.State.Holding_at_limit
        elif stringdata == "0x40":
            state = self.State.Holding_limit_time
        elif stringdata == "0x50":
            state = self.State.Holding_current_temperature
        else:
            raise LinkamT95Error(f"Status Bytes'{stringdata}'は想定外の形式をしています")

        return state

    def _check_Error(self, errorcode: int) -> None:
        """エラー情報をバイト列から読み取ってエラーがあれば警告

        Parameter
        ---------
        bytedata:
            エラー情報を含むbyte型のデータ
        """
        # ビット列の各桁にエラー情報が入っているので1つずつ確かめる(1になってたらエラー)
        if (errorcode & 0b00000001) != 0:
            logger.warning(
                "Cooling rate is too fast : Cooling rate cannot be maintained"
            )
        if (errorcode & 0b00000010) != 0:
            logger.warning(
                "Open circuit : Stage not connected or sensor is open circuit"
            )
        if (errorcode & 0b00000100) != 0:
            logger.warning(
                "Power surge : Current protection has been set due to an overload"
            )
        if (errorcode & 0b00001000) != 0:
            logger.warning(
                "No Exit 300 : TS 1500 tried to exit profile at a temperature > 300°"
            )
        # if (errorcode & 0b00010000) !=0: このエラーは存在しない
        if (errorcode & 0b00100000) != 0:
            logger.warning("Link error : Problem with the RS 232 data transmissin")
        # if (errorcode & 0b01000000) !=0: このエラーは存在しない
        # if (errorcode & 0b10000000) !=0: これは常にTrue

    def _read_pump_statusbyte(self, intdata: int) -> int:
        """窒素ガス速度を読む

        Parameters
        ----------
        intdata: int
            窒素ガス速度の情報を持つデータ
        """
        # なぜかガス速度+0x80で返ってくるので引き算
        pump_speed = intdata - 0x80
        # 0～30で帰ってくるデータをタッチパネルと同じ0～100に変換する
        pump_speed = math.ceil(pump_speed / 3 * 10)

        return pump_speed
