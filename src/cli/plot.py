import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

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


DEFAULT_INFO = {
    "line": False,
    "xlog": False,
    "ylog": False,
    "renew_interval": 1,
    "legend": False,
    "flowwidth": 0,
}


class PlotWindow:
    def __init__(
        self,
        data: dict[str, tuple[list[float], list[float]]] | None = None,
        info: dict | None = None,
    ) -> None:
        self._data = data if data is not None else {"default": ([], [])}
        self._info = (
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
