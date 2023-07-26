"""
LinkamT95をマクロから動かすコントローラー
新しいLinkamT95はシリアルポートが無くなったので使えないかも
"""
from __future__ import annotations

import dataclasses
import threading
import time
from logging import getLogger
from typing import List, Tuple

from measure.error import SSRError
from measure.masurement import MeasurementManager, MeasurementState

from .io import LinkamT95IO

logger = getLogger(__name__)


class LinkamT95ControllerError(SSRError):
    """LinkamT95Controller関係のエラー"""


class LinkamT95ManualController:
    """LinkamT95を制御するためのクラス

    _T95: LinkamT95IO
        このインスタンスを通してLinkamT95と通信する
    """

    _T95: LinkamT95IO = LinkamT95IO()
    _target_temperature = 0

    def connect(self, COMPORT: str) -> None:
        """機器への接続

        Parameters
        ----------
        COMPORT: str
            機器のシリアルポート番号(device managerなどで確認できる)
        """
        self._T95.connect(COMPORT)

    def run_program(self, temperature: int, temp_per_min: int, lnp_speed: int) -> None:
        """温度スイーププログラムを実行

        Parameters
        ----------
        temperature:
            目的温度
        temp_per_min:
            昇温速度(1分に何度変化させるか)
        lnp_speed:
            窒素フロー速度、0~100で設定 autoなら-1
        """
        self._target_temperature = temperature
        self._T95.set_limit_temperature(temperature)
        self._T95.set_rate(temp_per_min)
        self._T95.set_lnp_speed(lnp_speed)
        self._T95.start()

    def get_status(self) -> Tuple[bool, int]:
        """LinkamT95の状態を取得

        Returns
        -------
        (has_reached_target_temperature,temperature): tuple[bool,float]
            has_reached_target_temperature: 目的温度に到達したらTrue
            temperature: 温度(この温度はステージ下部の温度なので測定にそのまま使えるものではない)
        """
        # pump_speedの情報はいらないと判断して捨てた
        state, temperature, _ = self._T95.read_status()
        if (
            (state == LinkamT95IO.State.Cooling)
            or (state == LinkamT95IO.State.Heating)
            or (state == LinkamT95IO.State.Stopped)
        ):
            has_reached_target_temperature = False
        elif state == LinkamT95IO.State.Holding_at_limit:
            if abs(self._target_temperature - temperature) < 10:
                has_reached_target_temperature = True
            else:
                has_reached_target_temperature = False
        else:
            raise LinkamT95ControllerError(f"read_status()の返り値'{state}'は想定外です。")

        return has_reached_target_temperature, temperature

    def stop(self):
        """停止"""
        self._T95.stop()


# LinkamT95AutoController用の温度シーケンス
@dataclasses.dataclass
class Sequence:
    temperature: int
    temp_per_min: int
    hold_time_min: int
    lnp_speed: int


class Timer:
    """温度に到達したあとに設定時間分だけ待つタイマー"""

    __time__start = None
    __hold__time = None

    def start(self, hold_time_min):
        self.__time__start = time.time()
        self.__hold__time = hold_time_min

    def is_completed(self) -> bool:
        return time.time() - self.__time__start >= self.__hold__time * 60


class SequenceList:
    """設定シーケンスを保持するリスト"""

    __index = 0
    __sequence_list: List[Sequence] = []

    def add_sequence(self, sequence: Sequence):
        self.__sequence_list.append(sequence)

    def get_next_sequence(self):
        """次のシーケンスを返す。終了時はNoneを返す"""
        if self.__index < len(self.__sequence_list):
            seq = self.__sequence_list[self.__index]
            self.__index += 1
            return seq
        else:
            return None


class LinkamT95AutoController:
    """LinkamT95の制御を自動で行うためのクラス

    Attributes
    ----------
    __controller: LinkamT95ManualController
        温度コントローラー本体、これに指示を出す
    __sequence_list: list[Sequence]
        温度シーケンスのリスト、最初にここにシーケンスを追加してから動かす
    __index: int
        温度シーケンスの何番目を実行しているかを示す番号
    """

    __controller = LinkamT95ManualController()
    __sequence_list = SequenceList()
    __now_sequence: Sequence = None
    __timer: Timer = None

    def connect(self, COMPORT: str):
        """LinkamT95への接続

        Parameter
        ---------
        COMPORT: str
            接続先ポート番号
        """
        self.__controller.connect(COMPORT)

    def add_sequence(self, T: int, hold: int, rate: int, lnp: int):
        """温度シーケンスの追加

        Parameters
        ----------
        T: int
            温度
        hold: int
            温度保持時間(分)
        rate: int
            温度変化率(℃/分)
        lnp:
            窒素速度(Autoは)
        """
        self.__sequence_list.add_sequence(
            Sequence(
                temperature=T,
                hold_time_min=hold,
                temp_per_min=rate,
                lnp_speed=lnp,
            )
        )

    def start_sequence(self):
        """温度シーケンスを実行"""
        # 測定が強制終了されたときにこっちも終了できるように測定Stateを取得しておく
        measurement_state = MeasurementManager.get_measurement_state()
        measure_thread = threading.Thread(
            target=LinkamT95AutoController._controller_thread,
            args=(self, measurement_state),
        )
        measure_thread.setDaemon(True)
        measure_thread.start()

    @staticmethod
    def _controller_thread(autoController: LinkamT95AutoController, measurement_state):
        # 別スレッドでLinkamを動かし続ける
        while True:
            time.sleep(3)
            # 測定が終了したときにはFalseが返ってくる
            if autoController.__update(measurement_state):
                autoController.stop()
                break

    def __update(self, measurement_state: MeasurementState):
        """次の処理を判断する"""
        if self.__now_sequence is None:
            # 一番最初は__now_sequenceがNoneなのでここが呼ばれる(はず)
            self.__now_sequence = self.__sequence_list.get_next_sequence()
            # シーケンス実行
            self.__controller.run_program(
                self.__now_sequence.temperature,
                self.__now_sequence.temp_per_min,
                self.__now_sequence.lnp_speed,
            )

        # 二回目以降はこっちが呼ばれる
        # self.__timerは目的温度に到達してからホールド時間になるまでを測るタイマー
        if self.__timer is not None:
            if self.__timer.is_completed():
                # ホールド時間になったら次の温度シーケンスへ
                next_sequence = self.__sequence_list.get_next_sequence()
                if next_sequence is not None:
                    self.__controller.run_program(
                        next_sequence.temperature,
                        next_sequence.temp_per_min,
                        next_sequence.lnp_speed,
                    )
                    self.__now_sequence = next_sequence
                    self.__timer = None
                else:
                    # 次の温度シーケンスがなければ終了(Falseを返す)
                    logger.info("temperature sequence completed ...")
                    return False
        else:
            # 目的温度に達するまではタイマーがNoneなのでこっちが呼ばれる
            # 今の状態を取得
            (has_reached_target_temperature, _) = self.__controller.get_status()
            # 目的温度に達したらタイマーを生成する
            if has_reached_target_temperature:
                self.__timer = self.Timer()
                self.__timer.start(self.__now_sequence.hold_time_min)

        # 測定が強制終了するような場合にはここが呼ばれる
        if measurement_state.has_finished_measurement():
            logger.info("temperature sequence stopped ...")
            return False
        return True

    def cancel_sequence(self):
        """中断"""
        self.__controller.stop()
        self.__sequence_list = self.SequenceList()
        self.__timer = self.Timer()
