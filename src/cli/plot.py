import time
from multiprocessing import Event, Process, Queue
from queue import Empty

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from measure.error import SSRError
from measure.plot import COLOR_MAP, Plot


class PlotWindow(Plot):
    def __init__(
        self, data: dict[str, tuple[list[float], list[float]]] | None = None
    ) -> None:
        self._data = data if data is not None else {"default": ([], [])}
        self._ln: dict[str, Line2D] = {}
        self._interval = 0.1

    def plot(self, info) -> None:
        plt.ion()
        self._fig = plt.figure(figsize=(9, 6))
        self._ax = self._fig.add_subplot(111)
        self._info = info

        if info["xlog"]:
            self._ax.set_xscale("log")
        if info["ylog"]:
            self._ax.set_yscale("log")

        self.i = 0
        for k, v in self._data.items():
            self._ln[k] = self._ax.plot(
                v[0],
                v[1],
                marker=".",
                color=COLOR_MAP[self.i % len(COLOR_MAP)],
                label=k,
                linestyle=None if info["line"] else "None",
            )[0]
            self.i += 1

        if info["legend"]:
            if self.i > 20:
                ncol = 2
                self._fig.set_size_inches(11.5, 6)
                self._fig.subplots_adjust(right=0.7, left=0.1, top=0.95, bottom=0.1)
            else:
                ncol = 1
                self._fig.set_size_inches(10, 6)
                self._fig.subplots_adjust(right=0.8, left=0.1, top=0.95, bottom=0.1)
            self._ax.legend(
                bbox_to_anchor=(1.05, 1),
                loc="upper left",
                borderaxespad=0,
                fontsize=12,
                ncol=ncol,
            )
        self._fig.canvas.draw_idle()
        self._fig.canvas.flush_events()

    def append(self, key: str, x: float, y: float) -> bool:
        if not self.is_active():
            return False

        if not key in self._data:
            self._ln[key] = self._ax.plot(
                [x],
                [y],
                marker=".",
                color=COLOR_MAP[self.i % len(COLOR_MAP)],
                label=key,
                linestyle=None if self._info["line"] else "None",
            )[0]
            self.i += 1
            if self._info["legend"] and self.i > 20:
                self._fig.set_size_inches(11.5, 6)
                self._fig.subplots_adjust(right=0.7, left=0.1, top=0.95, bottom=0.1)
                self._ax.legend(
                    bbox_to_anchor=(1.05, 1),
                    loc="upper left",
                    borderaxespad=0,
                    fontsize=12,
                    ncol=2,
                )
            return True

        xarr, yarr = self._data[key]
        xarr.append(x)
        yarr.append(y)
        self._ln[key].set_data(xarr, yarr)
        self._ax.set_xlim(min(xarr), max(xarr))
        self._ax.set_ylim(min(yarr), max(yarr))
        self._fig.canvas.draw_idle()
        return True

    def is_active(self):
        return len(plt.get_fignums()) != 0

    def close(self) -> None:
        plt.close()

    def flush_events(self):
        if self.is_active():
            self._fig.canvas.flush_events()


def plot_window(info, q: Queue, close):
    pw = PlotWindow()
    pw.plot(info)

    while True:
        if close.is_set():
            break
        if not pw.is_active():
            break

        try:
            (x, y, label) = q.get_nowait()
            pw.append(label, x, y)
        except Empty:
            pass

        pw.flush_events()
        time.sleep(0.033)


class PlotAgentError(SSRError):
    pass


# TODO: remove it when we start measuring in a background process
class PlotAgency:
    def __init__(self) -> None:
        self.process = None
        self.info = {
            "line": False,
            "xlog": False,
            "ylog": False,
            "renew_interval": 1,
            "legend": False,
            "flowwidth": 0,
        }

    def run(self) -> None:
        self.queue = Queue(maxsize=5)
        self.close_event = Event()
        self.process = Process(
            target=plot_window, args=(self.info, self.queue, self.close_event)
        )
        self.process.start()

    def set_info(
        self,
        line=False,
        xlog=False,
        ylog=False,
        renew_interval=1,
        legend=False,
        flowwidth=0,
    ) -> None:
        if self.process is not None:
            raise PlotAgentError("set_infoはrunの前に呼ぶ必要があります")
        if type(line) is not bool:
            raise PlotAgentError("set_plot_infoの引数に問題があります: lineの値はboolです")
        if type(xlog) is not bool or type(ylog) is not bool:
            raise PlotAgentError("set_plot_infoの引数に問題があります: xlog,ylogの値はboolです")
        if type(legend) is not bool:
            raise PlotAgentError("set_plot_infoの引数に問題があります: legendの値はboolです")
        if type(flowwidth) is not float and type(flowwidth) is not int:
            raise PlotAgentError("set_plot_infoの引数に問題があります: flowwidthの型はintかfloatです")
        if flowwidth < 0:
            raise PlotAgentError("set_plot_infoの引数に問題があります: flowwidthの値は0以上にする必要があります")
        if type(renew_interval) is not float and type(renew_interval) is not int:
            raise PlotAgentError(
                "set_plot_infoの引数に問題があります: renew_intervalの型はintかfloatです"
            )
        if renew_interval < 0:
            raise PlotAgentError(
                "set_plot_infoの引数に問題があります: renew_intervalの型は0以上にする必要があります"
            )

        self.info = {
            "line": line,
            "xlog": xlog,
            "ylog": ylog,
            "renew_interval": renew_interval,
            "legend": legend,
            "flowwidth": flowwidth,
        }

    def plot(self, x: float, y: float, label="default") -> None:
        self.queue.put((x, y, label))

    def pause(self) -> None:
        pass

    def close(self) -> None:
        self.close_event.set()
        self.process.join()

    def is_active(self) -> bool:
        return self.process.is_alive()
