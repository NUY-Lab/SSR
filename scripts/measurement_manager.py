"""
ユーザーのマクロを受けとって動かす
ユーザーのマクロ側から呼び出せる関数などはほとんどここにあります
一部処理はmeasurement_manager_supportに切り出しています
"""
import msvcrt
import sys
import threading
import time
from logging import getLogger
from typing import Optional, Union

import calibration as calib
from measurement_manager_support import (
    CommandReceiver,
    FileManager,
    MeasurementState,
    MeasurementStep,
    PlotAgency,
)
from variables import USER_VARIABLES

logger = getLogger(__name__)


def start_macro(macro) -> None:
    """measurement_manager起動"""
    global _measurement_manager
    _measurement_manager = MeasurementManager(macro)
    _measurement_manager.measure_start()


def finish() -> None:
    """測定を終了させる"""
    logger.debug("finish is called")
    _measurement_manager.is_measuring = False


def set_file_name(filename: str, add_date: bool = True) -> None:
    """ファイル名をセット

    Parameter
    ---------
    filename : str
        ファイル名
    add_date : bool
        ファイル名の先頭に日付をつけるかどうか
    """
    _measurement_manager.file_manager.set_filename(filename, add_date)


def set_calibration(filepath_calib: Optional[str] = None) -> None:
    """この関数は非推奨です。calibration.pyを作ったのでそちらをから呼んでください

    プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み
    """
    global calibration_manager
    calibration_manager = calib.TMRCalibrationManager()
    if filepath_calib is None:
        calibration_manager.set_shared_calib_file()
    else:
        calibration_manager.set_own_calib_file(filepath_calib)


def calibration(x: float) -> float:
    """この関数は非推奨です。calibration.pyを作ったのでそちらをから呼んでください

    プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す
    """
    return calibration_manager.calibration(x)


def set_label(label: str) -> None:
    """ラベルをファイルに書き込み"""
    if _measurement_manager.state.current_step != MeasurementStep.START:
        logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.file_manager.write(label + "\n")


def write_file(text: str) -> None:
    """ファイルに書き込み"""
    _measurement_manager.file_manager.write(text)


def set_plot_info(
    line=False, xlog=False, ylog=False, renew_interval=1, legend=False, flowwidth=0
) -> None:  # プロット情報の入力
    """グラフ描画プロセスに渡す値はここで設定する.

    __plot_infoが辞書型なのはアンパックして引数に渡すため

    Parameter
    ---------

    line: bool
        プロットに線を引くかどうか

    xlog,ylog :bool
        対数軸にするかどうか

    renew_interval : float (>0)
        グラフの更新間隔(秒)

    legend : bool
        凡例をつけるか. (凡例の名前はlabelの値)

    flowwidth : float (>0)
        これが0より大きい値のとき. グラフの横軸は固定され､横にプロットが流れるようなグラフになる.
    """

    if _measurement_manager.state.current_step != MeasurementStep.START:
        logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.plot_agency.set_plot_info(
        line=line,
        xlog=xlog,
        ylog=ylog,
        renew_interval=renew_interval,
        legend=legend,
        flowwidth=flowwidth,
    )


def dont_make_file():
    """ファイルを作成しないときはこれを呼ぶ

    これを呼んだあとにファイル操作系の関数を呼ぶとエラーを吐く
    """
    if _measurement_manager.state.current_step != MeasurementStep.START:
        logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.dont_make_file()


def save_data(*data: Union[tuple, str]) -> None:
    """データのセーブ"""
    logger.warning("関数save_dataは非推奨です。 saveを使ってください")
    save(*data)


def save(*data: Union[tuple, str]) -> None:  # データ保存
    """引数のデータをファイルに書き込む.

    この関数が呼ばれるごとに書き込みの反映( __savefile.flush)をおこなっているので途中で測定が落ちてもそれまでのデータは残るようになっている.
    stringの引数にも対応しているので､測定のデータは測定マクロ側でstringで保持しておいて最後にまとめて書き込むことも可能.

    Parameter
    ---------

    data : tuple or string
        書き込むデータ
    """
    if not bool(
        _measurement_manager.state.current_step
        & (MeasurementStep.UPDATE | MeasurementStep.END)
    ):
        logger.warning(sys._getframe().f_code.co_name + "はupdateもしくはend関数内で用いてください")
    _measurement_manager.file_manager.save(*data)


plot_data_flag = False


def plot_data(x: float, y: float, label: str = "default") -> None:  # データをグラフにプロット
    global plot_data_flag
    if not plot_data_flag:
        logger.warning("plot_dataは非推奨です。plotを使ってください")
        plot_data_flag = True
    plot(x, y, label)


def plot(x: float, y: float, label: str = "default") -> None:
    """データをグラフ描画プロセスに渡す.

    labelが変わると色が変わる
    __share_listは測定プロセスとグラフ描画プロセスの橋渡しとなるリストでバッファーの役割をする

    Parameter
    ---------

    x,y : float
        プロットのx,y座標

    label : string or float
        プロットの識別ラベル.
        これが同じだと同じ色でプロットしたり､線を引き設定のときは線を引いたりする.
    """

    if _measurement_manager.state.current_step != MeasurementStep.UPDATE:
        logger.warning(sys._getframe().f_code.co_name + "はstartもしくはupdate関数内で用いてください")

    if _measurement_manager.is_measuring:
        _measurement_manager.plot_agency.plot(x, y, label)


def no_plot() -> None:
    """プロット画面を出さないときに呼ぶ"""
    if _measurement_manager.state.current_step != MeasurementStep.START:
        logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.plot_agency = PlotAgency.NoPlotAgency()


class MeasurementManager:
    """測定の管理、マクロの各関数の呼び出し"""

    file_manager = None
    plot_agency = None
    command_receiver = None
    state = MeasurementState()
    is_measuring = False
    _dont_make_file = False

    @classmethod
    def set_measurement_state(cls, state: MeasurementState):
        cls.state = state

    @classmethod
    def get_measurement_state(cls) -> MeasurementState:
        return cls.state

    def __init__(self, macro) -> None:
        self.macro = macro
        self.file_manager = FileManager(USER_VARIABLES.DATADIR)
        self.plot_agency = PlotAgency()
        self.command_receiver = CommandReceiver(self.state)
        self.set_measurement_state(self.state)

    def measure_start(self) -> None:
        """測定のメインとなる関数.

        測定マクロに書かれた各関数はMAIN.pyによってここに渡されて
        ここでそれぞれの関数を適切なタイミングで呼んでいる
        """
        logger.debug("measurement start")
        self.state.current_step = MeasurementStep.READY

        while msvcrt.kbhit():  # 既に入っている入力は消す
            msvcrt.getwch()

        self.state.current_step = MeasurementStep.START

        if self.macro.start is not None:
            self.macro.start()

        if not self._dont_make_file:
            self.file_manager.create_file(
                do_make_folder=(self.macro.split is not None),
            )  # ファイル作成

        self.plot_agency.run_plot_window()  # グラフウィンドウの立ち上げ

        while msvcrt.kbhit():  # 既に入っている入力は消す
            msvcrt.getwch()

        if self.macro.on_command is not None:
            self.command_receiver.initialize()

        print("measuring start...")
        self.state.current_step = MeasurementStep.UPDATE

        self.is_measuring = True
        while True:  # 測定終了までupdateを回す
            if not self.is_measuring:
                break
            command = self.command_receiver.get_command()
            if command is None:
                flag = self.macro.update()
                if (flag is not None) and not flag:
                    logger.debug("return False from update function")
                    self.is_measuring = False
            else:
                self.macro.on_command(command)  # コマンドが入っていればコマンドを呼ぶ

            if self.plot_agency.is_plot_window_forced_terminated():
                logger.debug("measurement has finished because plot window closed")
                self.is_measuring = False

        self.state.current_step = MeasurementStep.FINISH_MEASURE
        self.plot_agency.stop_renew_plot_window()

        while msvcrt.kbhit():  # 既に入っている入力は消す
            msvcrt.getwch()

        print("measurement has finished...")

        if self.macro.end is not None:
            self.state.current_step = MeasurementStep.END
            self.macro.end()

        if not self._dont_make_file:
            self.file_manager.close()  # ファイルはend関数の後で閉じる

        self.state.current_step = MeasurementStep.AFTER

        if not self._dont_make_file:
            if self.macro.split is not None:
                self.macro.split(self.file_manager.filepath)

            if self.macro.after is not None:
                self.macro.after(self.file_manager.filepath)

        self.end()

    def end(self):
        """終了処理. コンソールからの終了と､グラフウィンドウを閉じたときの終了の2つを実行できるようにスレッドを用いる"""

        def wait_enter():  # コンソール側の終了
            nonlocal endflag, windowclose  # nonlocalを使うとクロージャーになる
            input("enter and close window...")  # エンターを押したら次へ進める
            endflag = True
            windowclose = True

        def wait_closewindow():  # グラフウィンドウからの終了
            nonlocal endflag
            while True:
                # print(self.plot_agency.is_plot_window_alive())
                if not self.plot_agency.is_plot_window_alive():
                    break
                time.sleep(0.2)
            endflag = True

        endflag = False
        windowclose = False

        thread1 = threading.Thread(target=wait_closewindow)
        thread1.daemon = True
        thread1.start()

        time.sleep(0.1)

        endflag = (
            False  # 既にグラフが消えていた場合はwait_enterを終了処理とする. それ以外の場合はwait_closewindowも終了処理とする
        )

        thread2 = threading.Thread(target=wait_enter)
        thread2.daemon = True
        thread2.start()

        while True:
            if endflag:
                if not windowclose:
                    self.plot_agency.close()
                break
            time.sleep(0.05)

    def dont_make_file(self):
        self._dont_make_file = True
