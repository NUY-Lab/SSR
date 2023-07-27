"""
ユーザーのマクロを受けとって動かす
ユーザーのマクロ側から呼び出せる関数などはほとんどここにあります
一部処理はmeasurement_manager_supportに切り出しています
"""
import msvcrt
import sys
from logging import getLogger

from cli.plot import PlotAgency

from .measurement_support import (
    CommandReceiver,
    FileManager,
    MeasurementState,
    MeasurementStep,
)
from .util import get_date_text
from .variable import USER_VARIABLES

logger = getLogger(__name__)


def start_macro(macro, console) -> None:
    """measurement_manager起動"""
    global _measurement_manager
    _measurement_manager = MeasurementManager(macro, console)
    _measurement_manager.measure_start()


def finish() -> None:
    """測定を終了させる"""
    logger.debug("finish is called")
    _measurement_manager.is_measuring = False


def set_file(filename: str = None, add_date=True):
    """ファイル名をセット

    Parameter
    ---------
    filename : str
        ファイル名
    add_date : bool
        ファイル名の先頭に日付をつけるかどうか
    """

    if filename is not None and add_date:
        filename = f"{filename}{get_date_text()}.txt"

    if filename is not None:
        _measurement_manager.file_manager.set_file(
            filepath=f"{USER_VARIABLES.DATADIR}/{filename}"
        )
    else:
        _measurement_manager.file_manager.set_file(filepath=None)


def set_label(label: str) -> None:
    """ラベルをファイルに書き込み"""
    if _measurement_manager.state.current_step != MeasurementStep.START:
        logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    _measurement_manager.file_manager.write(label + "\n")


def write_file(text: str) -> None:
    """ファイルに書き込み"""
    _measurement_manager.file_manager.write(text)


def set_plot_info(
    line=False,
    xlog=False,
    ylog=False,
    renew_interval=1,
    legend=False,
    flowwidth=0,
) -> None:
    """プロット情報の入力

    グラフ描画プロセスに渡す値はここで設定する.
    __plot_infoが辞書型なのはアンパックして引数に渡すため

    Parameter
    ---------

    line: bool
        プロットに線を引くかどうか
    xlog, ylog: bool
        対数軸にするかどうか
    renew_interval: float (>0)
        グラフの更新間隔(秒)
    legend: bool
        凡例をつけるか. (凡例の名前はlabelの値)
    flowwidth: float (>0)
        これが0より大きい値のとき. グラフの横軸は固定され､横にプロットが流れるようなグラフになる.
    """

    if _measurement_manager.state.current_step != MeasurementStep.START:
        logger.warning(sys._getframe().f_code.co_name + "はstart関数内で用いてください")
    # _measurement_manager.plot_agency.set_plot_info(
    _measurement_manager.plot_agency.set_info(
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


def save_data(*data: tuple | str) -> None:
    """データのセーブ"""
    logger.warning("関数save_dataは非推奨です。 saveを使ってください")
    save(*data)


def save(*data: tuple | str) -> None:  # データ保存
    """引数のデータをファイルに書き込む.

    この関数が呼ばれるごとに書き込みの反映をおこなっているので
    途中で測定が落ちてもそれまでのデータは残るようになっている.
    stringの引数にも対応しているので､測定のデータは測定マクロ側でstringで
    保持しておいて最後にまとめて書き込むことも可能.

    Parameter
    ---------

    data: tuple or string
        書き込むデータ
    """
    if not bool(
        _measurement_manager.state.current_step
        & (MeasurementStep.UPDATE | MeasurementStep.END)
    ):
        logger.warning(sys._getframe().f_code.co_name + "はupdateもしくはend関数内で用いてください")
    _measurement_manager.file_manager.save(*data)


plot_data_flag = False


# データをグラフにプロット
def plot_data(x: float, y: float, label: str = "default") -> None:
    global plot_data_flag
    if not plot_data_flag:
        logger.warning("plot_dataは非推奨です。plotを使ってください")
        plot_data_flag = True
    plot(x, y, label)


def plot(x: float, y: float, label="default") -> None:
    """データをグラフ描画プロセスに渡す.

    labelが変わると色が変わる
    __share_listは測定プロセスとグラフ描画プロセスの橋渡しとなるリストでバッファーの役割をする

    Parameter
    ---------

    x, y: float
        プロットのx,y座標
    label: string | float
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


def log(msg: str) -> None:
    _measurement_manager.console.log(msg)


def _get_measurement_manager() -> "MeasurementManager":
    return _measurement_manager


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

    def __init__(self, macro, console) -> None:
        self.macro = macro
        self.file_manager = FileManager()
        self.plot_agency = PlotAgency()
        self.command_receiver = CommandReceiver(self.state)
        self.set_measurement_state(self.state)
        self.console = console

    def measure_start(self) -> None:
        """測定のメインとなる関数.

        測定マクロに書かれた各関数はMAIN.pyによってここに渡されて
        ここでそれぞれの関数を適切なタイミングで呼んでいる
        """
        logger.debug("measurement start")
        self.state.current_step = MeasurementStep.READY

        # 既に入っている入力は消す
        while msvcrt.kbhit():
            msvcrt.getwch()

        self.state.current_step = MeasurementStep.START

        if self.macro.start is not None:
            self.macro.start()
        if (not self._dont_make_file) and (self.file_manager.filepath is None):
            self.file_manager.set_file(
                filepath=f"{USER_VARIABLES.DATADIR}/{get_date_text()}.txt"
            )

        # グラフウィンドウの立ち上げ
        # self.plot_agency.run_plot_window()
        self.plot_agency.run()

        # 既に入っている入力は消す
        while msvcrt.kbhit():
            msvcrt.getwch()

        if self.macro.on_command is not None:
            self.command_receiver.initialize()

        self.console.log("measuring start...")
        self.state.current_step = MeasurementStep.UPDATE

        self.is_measuring = True

        # 測定終了までupdateを回す
        while True:
            if not self.is_measuring:
                break
            command = self.command_receiver.get_command()
            if command is None:
                flag = self.macro.update()
                if (flag is not None) and not flag:
                    logger.debug("return False from update function")
                    self.is_measuring = False
            else:
                # コマンドが入っていればコマンドを呼ぶ
                self.macro.on_command(command)

            # if self.plot_agency.is_plot_window_forced_terminated():
            if not self.plot_agency.is_active():
                logger.debug("measurement has finished because plot window closed")
                self.is_measuring = False

        self.state.current_step = MeasurementStep.FINISH_MEASURE
        # self.plot_agency.stop_renew_plot_window()
        self.plot_agency.pause()

        # 既に入っている入力は消す
        while msvcrt.kbhit():
            msvcrt.getwch()

        self.console.log("measurement has finished...")

        if self.macro.end is not None:
            self.state.current_step = MeasurementStep.END
            self.macro.end()

        # ファイルはend関数の後で閉じる
        if not self._dont_make_file:
            self.file_manager.close()

        self.state.current_step = MeasurementStep.AFTER

        if not self._dont_make_file:
            if self.macro.split is not None:
                self.macro.split(self.file_manager.filepath)

            if self.macro.after is not None:
                self.macro.after(self.file_manager.filepath)

    def dont_make_file(self):
        self._dont_make_file = True
