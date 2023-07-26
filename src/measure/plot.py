"""
プロットの処理と終了入力待ちは測定と別プロセスで行って非同期にする
(データ数が増えてプロットに時間がかかっても測定に影響が出ないようにする)
"""
import time
from multiprocessing import Lock

import matplotlib.pyplot as plt

# TODO: UI側に移動する

# 色の配列
COLOR_MAP = (
    "black",
    "red",
    "green",
    "blue",
    "orange",
    "deepskyblue",
    "purple",
    "gray",
    "saddlebrown",
    "crimson",
    "limegreen",
    "royalblue",
    "orangered",
    "skyblue",
    "darkslategray",
    "deeppink",
    "darkslateblue",
    "olivedrab",
    "darkgoldenrod",
    "brown",
    "teal",
    "lightgray",
)


def start_plot_window(
    share_list: list[tuple[float, float, str]],
    isfinish: bool,
    lock: Lock,
    plot_info: dict,
) -> None:
    """別プロセスで最初に実行される場所"""
    PlotWindow(share_list, isfinish, lock, **plot_info).run()


class PlotWindow:
    """測定データをグラフにするクラス

    Variables
    ---------

    share_list: list
        測定したデータを一時的に保管しておく場所
        非同期処理のため測定とプロットがずれるので, そのためにバッファーのようなものを挟む必要がある
        測定側で測定データをshare_listに詰めていく
        PlotWindowはshare_listのデータを取り込んでプロットした後に中身を消す
        この処理が衝突しないようにlock(セマフォ)をかけて排他制御する
    lock:
        プロセス間の共有ファイルを同時に触らないためのロック
    isfinish:
        測定が終了した可動化を判定.
        測定が終了したらmeasurementManager側でisfinish=1が代入される
    interval: float
        グラフの更新間隔
    legend: bool
        凡例を表示するかどうか
    linestyle: string
        グラフに線をつけるかどうか
    """

    _figure = None
    _ax = None

    def __init__(
        self,
        share_list,
        isfinish,
        lock,
        xlog,
        ylog,
        renew_interval,
        flowwidth,
        line,
        legend,
    ) -> None:
        self.share_list = share_list
        self.lock = lock
        self.interval = renew_interval
        self.flowwidth = flowwidth
        self.isfinish = isfinish
        self.legend = legend
        self.linestyle = None if line else "None"

        # プロットウィンドウを表示
        plt.ion()
        self._figure, self._ax = plt.subplots(figsize=(9, 6))

        if xlog:
            plt.xscale("log")
        if ylog:
            plt.yscale("log")

    def run(self) -> None:
        """プロットの処理をループで回す"""
        interval: int = self.interval
        # 一定時間ごとに更新
        while True:
            self.renew_window()
            # 終了していたらbreak
            if self.isfinish.value == 1 or (not plt.get_fignums()):
                break
            time.sleep(interval)

        if plt.get_fignums():
            plt.show(block=True)

    _count_label = 0
    linedict = {}
    max_x: float | None = None
    max_y: float | None = None
    min_x: float | None = None
    min_y: float | None = None

    def renew_window(self) -> None:
        """プロット画面の更新で呼ぶ関数"""

        # 共有リストにロックをかける
        self.lock.acquire()
        # share_listのコピーを作成.
        # (temp=share_listにすると参照になってしまうのでdel self.share_list[:]でtempも消えてしまう)
        temp = self.share_list[:]
        # 共有リストは削除
        del self.share_list[:]
        self.lock.release()

        # for文が1回も回らないことがあるのでここで宣言しておく
        xrelim = False
        yrelim = False

        for plotdata in temp:
            x_val, y_val, label = plotdata

            if label not in self.linedict:
                # 最初の一回だけは辞書に登録する
                xarray = [x_val]
                yaaray = [y_val]
                color = COLOR_MAP[(self._count_label) % len(COLOR_MAP)]
                self._count_label += 1
                # プロット
                (line,) = self._ax.plot(
                    xarray,
                    yaaray,
                    marker=".",
                    color=color,
                    label=label,
                    linestyle=self.linestyle,
                )
                # 辞書に追加
                lineobj = LineObj(line, xarray, yaaray)
                self.linedict[label] = lineobj

                if self.legend:
                    if self._count_label > 20:
                        ncol = 2
                        self._figure.set_size_inches(11.5, 6)
                        self._figure.subplots_adjust(
                            right=0.7, left=0.1, top=0.95, bottom=0.1
                        )
                    else:
                        ncol = 1
                        self._figure.set_size_inches(10, 6)
                        self._figure.subplots_adjust(
                            right=0.8, left=0.1, top=0.95, bottom=0.1
                        )
                    self._ax.legend(
                        bbox_to_anchor=(1.05, 1),
                        loc="upper left",
                        borderaxespad=0,
                        fontsize=12,
                        ncol=ncol,
                    )

            else:
                # 2回目以降は色をキーにして辞書からLineObjをとってくる
                lineobj = self.linedict[label]
                lineobj.xarray.append(x_val)
                lineobj.yaaray.append(y_val)
                lineobj.line.set_data(lineobj.xarray, lineobj.yaaray)

            # 今までの範囲の外にプロットしたときは範囲を更新
            if self.max_x is None:
                self.max_x = x_val
            elif self.max_x < x_val:
                self.max_x = x_val
                xrelim = True

            if self.max_y is None:
                self.max_y = y_val
            elif self.max_y < y_val:
                self.max_y = y_val
                yrelim = True

            if self.min_x is None:
                self.min_x = x_val
            elif self.min_x > x_val:
                self.min_x = x_val
                xrelim = True

            if self.min_y is None:
                self.min_y = y_val
            elif self.min_y > y_val:
                self.min_y = y_val
                yrelim = True

        if xrelim or yrelim:
            if self.flowwidth <= 0:
                # 範囲の更新
                if xrelim:
                    self._ax.set_xlim(self.min_x, self.max_x)
                if yrelim:
                    self._ax.set_ylim(self.min_y, self.max_y)
            else:
                # 横幅が決まっているときはそれに先頭に合わせて範囲を変更
                xmin = self.max_x - self.flowwidth
                self._ax.set_xlim(xmin, self.max_x)
                self._ax.set_ylim(self.min_y, self.max_y)

                # 範囲外のプロットは消す
                for line_obj in self.linedict.values():
                    xarray = line_obj.xarray
                    yaaray = line_obj.yaaray
                    cut = 0
                    for i, xvalue in enumerate(xarray):
                        if xvalue < xmin:
                            continue
                        else:
                            cut = max(i - 1, 0)
                            break
                    line_obj.xarray = xarray[cut:]
                    line_obj.yaaray = yaaray[cut:]

        # グラフを再描画するおまじない
        self._figure.canvas.flush_events()


class LineObj:
    """matplotlibでプロットしたグラフの線1つにつきこれが1つ作られる"""

    def __init__(self, line, xarray, yaaray):
        self.line = line
        self.xarray = xarray
        self.yaaray = yaaray
