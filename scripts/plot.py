"""
    プロットの処理と終了入力待ちは測定と別プロセスで行って非同期にする
    (データ数が増えてプロットに時間がかかっても測定に影響が出ないようにする)

"""
import time
from multiprocessing import Lock
from multiprocessing.managers import ListProxy
from typing import List, Optional

import matplotlib.pyplot as plt

# 色の配列(matplotlibのデフォルトでもいいけどすこし見ずらいので自作)
colormap: tuple[str] = (
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
    share_list: ListProxy,#ListProxy[tuple[float, float, str]],
    isfinish: bool,
    lock: Lock,
    plot_info: dict,
) -> None:
    """
    別プロセスで最初に実行される場所
    """

    PlotWindow(share_list, isfinish, lock, **plot_info).run()  # インスタンス作成, 実行


class PlotWindow:
    """測定データをグラフにするクラス

    Variables
    ---------
    share_list :multiprocessing.managers.ListProxy
        測定したデータを一時的に保管しておく場所
        非同期処理のため測定とプロットがずれるので, そのためにバッファーのようなものを挟む必要がある
        測定側で測定データをshare_listに詰めていく
        PlotWindowはshare_listのデータを取り込んでプロットした後に中身を消す
        この処理が衝突しないようにlock(セマフォ)をかけて排他制御する
        最初、このリストは測定側のプロセスで作成され、plotプロセスに渡されて2つのプロセスで共有する

    lock:
        プロセス間の共有ファイルを同時に触らないためのロック

    isfinish:
        測定が終了した可動化を判定.
        測定が終了したらmeasurementManager側でisfinish=1が代入される

    interval :float
        グラフの更新間隔

    legend : bool
        凡例を表示するかどうか

    linestyle : string
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
    ) -> None:  # コンストラクタ
        self.share_list = share_list
        self.lock = lock
        self.interval = renew_interval
        self.flowwidth = flowwidth
        self.isfinish = isfinish
        self.legend = legend
        self.linestyle = None if line else "None"

        # プロットウィンドウを表示
        plt.ion()  # ここはコピペ plotウィンドウを更新するために必要なもの(多分)
        self._figure, self._ax = plt.subplots(figsize=(9, 6))  # ここはコピペ

        if xlog:
            plt.xscale("log")  # 横軸をlogスケールに
        if ylog:
            plt.yscale("log")  # 縦軸をlogスケールに

    def run(self) -> None:
        """プロットの処理をループで回す"""
        interval: int = self.interval
        while True:  # 一定時間ごとに更新
            self.renew_window() #plotウィンドウの更新
            if self.isfinish.value == 1 or (not plt.get_fignums()):  # 終了していたらbreak
                break
            time.sleep(interval)

        if plt.get_fignums(): #ウィンドウが消えているかを判定(多分)
            plt.show(block=True) #plt.show()を呼ぶことで このプロセスが落ちないようにしている (plotウィンドウを閉じるとこのプロセスは終了する)

    _count_label: int = 0
    linedict = {}
    max_x: Optional[float] = None
    max_y: Optional[float] = None
    min_x: Optional[float] = None
    min_y: Optional[float] = None

    def renew_window(self) -> None:
        """プロット画面の更新で呼ぶ関数"""
        self.lock.acquire()  # 共有リストにロックをかける
        # share_listのコピーを作成.(temp=share_listにすると参照になってしまうのでdel self.share_list[:]でtempも消えてしまう)
        temp = self.share_list[:]  # [i for i in self.share_list]はかなり重い
        del self.share_list[:]  # 共有リストは削除
        self.lock.release()  # ロック解除

        xrelim = False  # for文が1回も回らないことがあるのでここで宣言しておく
        yrelim = False

        for plotdata in temp:  # tempの中身をプロット
            x_val, y_val, label = plotdata

            if label not in self.linedict:  # 最初の一回だけは辞書に登録する
                xarray = [x_val]
                yaaray = [y_val]
                color = colormap[(self._count_label) % len(colormap)] 
                self._count_label += 1
                (line,) = self._ax.plot(
                    xarray,
                    yaaray,
                    marker=".",
                    color=color,
                    label=label,
                    linestyle=self.linestyle,
                )  # プロット
                lineobj = self.LineObj(line, xarray, yaaray)  # プロットデータ(lineobj)を辞書に追加 (後でlineobjを呼び出してデータを追加する)
                self.linedict[label] = lineobj

                if self.legend: #凡例をつける (ここの処理はちゃんと試していないからうまく動くかわからない)
                    if self._count_label > 20: #凡例が20を超えたら2行
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

            else:  # 2回目以降は色をキーにして辞書からLineObjをとってくる
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
                # self.flowwidth>0のときはxの最大値から最大値-flowwidthの範囲を表示 (ここの処理はちゃんと試していないからうまく動くかわからない)
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

        self._figure.canvas.flush_events()  # グラフを再描画するおまじない

    class LineObj:
        """matplotlibでプロットしたグラフの線1つにつきこれが1つ作られる"""

        def __init__(self, line, xarray, yaaray):
            self.line = line
            self.xarray = xarray
            self.yaaray = yaaray
