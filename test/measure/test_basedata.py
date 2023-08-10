import pytest

from measure.basedata import BaseData, BaseDataError


def test1():
    class Data(BaseData):
        x: "[mV]"
        y: "[m]"

    data = Data(1, 2)
    assert data.x == 1
    assert data.y == 2

    data.x = 0
    assert data.x == 0
    assert list(data) == [0, 2]
    assert Data.to_label() == "0:x [mV],  1:y [m]"

    with pytest.raises(BaseDataError):
        # 存在しない属性に代入
        data.z = 100


def test2():
    # 不正な型定義
    with pytest.raises(BaseDataError):

        class Data(BaseData):
            x: "[mV]"
            y: "[mV]" = 10

    with pytest.raises(BaseDataError):

        class Data(BaseData):
            x: "[mV]"
            y: int

    with pytest.raises(BaseDataError):

        class Data(BaseData):
            x = 10
            y = None

    with pytest.raises(BaseDataError):

        class Data(BaseData):
            x = "[mV]"
            y = "[m]"


def test3():
    # キーワード指定で逆に入れても問題ないか
    class Data(BaseData):
        x: "[mV]"
        y: "[m]" = 2

    data = Data(y=10, x=19)
    assert data.x == 19
    assert data.y == 10


def test3():
    # アノテーションが空文字
    class Data(BaseData):
        x: ""

    assert Data.to_label() == "0:x "
    data = Data(1)
    assert data.x == 1


def test4():
    # コンストラクタを書いた場合
    class Data(BaseData):
        x: "[mV]"
        y: "[m]"

        def __init__(self, x) -> None:
            self.x = 100
            super().__init__()

    data = Data(0)
    assert data.x == 100
