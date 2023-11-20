from logging import getLogger
from tkinter import Tk, Toplevel

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

logger = getLogger(__name__)

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


class Plot:
    def __init__(self, master: Tk, data, info) -> None:
        self.data = data if data is not None else {"default": ([], [])}
        self.info = (
            info
            if info is not None
            else {
                "line": False,
                "xlog": False,
                "ylog": False,
                "legend": False,
                "flowwidth": 0,
            }
        )
        self.ln: dict[str, Line2D] = {}
        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)

        if info["xlog"]:
            self.ax.set_xscale("log")
        if info["ylog"]:
            self.ax.set_yscale("log")

        self.i = 0
        for k, v in self.data.items():
            self.ln[k] = self.ax.plot(
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
                self.fig.set_size_inches(11.5, 6)
                self.fig.subplots_adjust(right=0.7, left=0.1, top=0.95, bottom=0.1)
            else:
                ncol = 1
                self.fig.set_size_inches(10, 6)
                self.fig.subplots_adjust(right=0.8, left=0.1, top=0.95, bottom=0.1)
            self.ax.legend(
                bbox_to_anchor=(1.05, 1),
                loc="upper left",
                borderaxespad=0,
                fontsize=12,
                ncol=ncol,
            )

        self.sub_window = Toplevel(master)
        self.sub_window.title("Plot")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.sub_window)
        self.canvas.get_tk_widget().pack()
        self.canvas.draw()

    def append(self, key, x, y):
        if not key in self.data:
            self.ln[key] = self.ax.plot(
                [x],
                [y],
                marker=".",
                color=COLOR_MAP[self.i % len(COLOR_MAP)],
                label=key,
                linestyle=None if self.info["line"] else "None",
            )[0]
            self.i += 1
            if self.info["legend"] and self.i > 20:
                self.fig.set_size_inches(11.5, 6)
                self.fig.subplots_adjust(right=0.7, left=0.1, top=0.95, bottom=0.1)
                self.ax.legend(
                    bbox_to_anchor=(1.05, 1),
                    loc="upper left",
                    borderaxespad=0,
                    fontsize=12,
                    ncol=2,
                )

        xarr, yarr = self.data[key]
        xarr.append(x)
        yarr.append(y)
        self.ln[key].set_data(xarr, yarr)
        self.ax.set_xlim(min(xarr), max(xarr))
        self.ax.set_ylim(min(yarr), max(yarr))
        self.fig.canvas.draw_idle()
