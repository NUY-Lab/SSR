"""
LinkamT95をマクロから動かすコントローラー
新しいLinkamT95はシリアルポートが無くなったので使えないかも
"""
from __future__ import annotations

import dataclasses
import threading
import time
from logging import getLogger

from measure.error import SSRError
from measure.measurement import State, _state

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

    def get_status(self) -> tuple[bool, int]:
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

    _time__start = None
    _hold__time = None

    def start(self, hold_time_min):
        self._time__start = time.time()
        self._hold__time = hold_time_min

    def is_completed(self) -> bool:
        return time.time() - self._time__start >= self._hold__time * 60


class SequenceList:
    """設定シーケンスを保持するリスト"""

    _index = 0
    _sequence_list: list[Sequence] = []

    def add_sequence(self, sequence: Sequence):
        self._sequence_list.append(sequence)

    def get_next_sequence(self):
        """次のシーケンスを返す。終了時はNoneを返す"""
        if self._index < len(self._sequence_list):
            seq = self._sequence_list[self._index]
            self._index += 1
            return seq
        else:
            return None


class LinkamT95AutoController:
    """LinkamT95の制御を自動で行うためのクラス

    Attributes
    ----------
    _controller: LinkamT95ManualController
        温度コントローラー本体、これに指示を出す
    _sequence_list: list[Sequence]
        温度シーケンスのリスト、最初にここにシーケンスを追加してから動かす
    _index: int
        温度シーケンスの何番目を実行しているかを示す番号
    """

    _controller = LinkamT95ManualController()
    _sequence_list = SequenceList()
    _now_sequence: Sequence = None
    _timer: Timer = None

    def connect(self, COMPORT: str):
        """LinkamT95への接続

        Parameter
        ---------
        COMPORT: str
            接続先ポート番号
        """
        self._controller.connect(COMPORT)

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
        self._sequence_list.add_sequence(
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
        measurement_state = _state()
        measure_thread = threading.Thread(
            target=LinkamT95AutoController._controller_thread,
            args=(self, measurement_state),
        )
        measure_thread.setDaemon(True)
        measure_thread.start()

    @staticmethod
    def _controller_thread(autoController: LinkamT95AutoController):
        # 別スレッドでLinkamを動かし続ける
        while True:
            time.sleep(3)
            # 測定が終了したときにはFalseが返ってくる
            if autoController._update():
                autoController.stop()
                break

    def _update(self):
        """次の処理を判断する"""
        if self._now_sequence is None:
            # 一番最初は__now_sequenceがNoneなのでここが呼ばれる(はず)
            self._now_sequence = self._sequence_list.get_next_sequence()
            # シーケンス実行
            self._controller.run_program(
                self._now_sequence.temperature,
                self._now_sequence.temp_per_min,
                self._now_sequence.lnp_speed,
            )

        # 二回目以降はこっちが呼ばれる
        # self.__timerは目的温度に到達してからホールド時間になるまでを測るタイマー
        if self._timer is not None:
            if self._timer.is_completed():
                # ホールド時間になったら次の温度シーケンスへ
                next_sequence = self._sequence_list.get_next_sequence()
                if next_sequence is not None:
                    self._controller.run_program(
                        next_sequence.temperature,
                        next_sequence.temp_per_min,
                        next_sequence.lnp_speed,
                    )
                    self._now_sequence = next_sequence
                    self._timer = None
                else:
                    # 次の温度シーケンスがなければ終了(Falseを返す)
                    logger.info("temperature sequence completed ...")
                    return False
        else:
            # 目的温度に達するまではタイマーがNoneなのでこっちが呼ばれる
            # 今の状態を取得
            (has_reached_target_temperature, _) = self._controller.get_status()
            # 目的温度に達したらタイマーを生成する
            if has_reached_target_temperature:
                self._timer = Timer()
                self._timer.start(self._now_sequence.hold_time_min)

        # 測定が強制終了するような場合にはここが呼ばれる
        if bool(_state() & (State.FINISH_MEASURE | State.END | State.AFTER)):
            logger.info("temperature sequence stopped ...")
            return False
        return True

    def cancel_sequence(self):
        """中断"""
        self._controller.stop()
        self._sequence_list = SequenceList()
        self._timer = Timer()
