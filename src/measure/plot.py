"""
プロットの処理と終了入力待ちは測定と別プロセスで行って非同期にする
(データ数が増えてプロットに時間がかかっても測定に影響が出ないようにする)
"""
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


class Plot:
    def plot(self) -> None:
        raise NotImplementedError()

    def append(self) -> None:
        raise NotImplementedError()

    def is_active(self) -> bool:
        raise NotImplementedError()
