import pytest

from basedata import BaseData


def test_BaseData_1():
    class Data(BaseData):
        x: "[mV]"
        y: "[m]"

    data = Data(x=1, y=2)
    assert data.x == 1
    assert data.y == 2
    data.x = 0
    assert data.x == 0
    assert list(data) == [0, 2]
    assert Data.to_label() == "0:x[mV],1:y[m]"

    with pytest.raises(BaseData.BaseDataError):
        data.z = 100  # 存在しない属性に代入


def test_BaseData_2():
    # 不正な型定義
    with pytest.raises(BaseData.BaseDataError):

        class Data(BaseData):
            x: "[mV]"
            y: "[mV]" = 10

    with pytest.raises(BaseData.BaseDataError):

        class Data(BaseData):
            x: "[mV]"
            y: int

    with pytest.raises(BaseData.BaseDataError):

        class Data(BaseData):
            x = 10
            y = None

    with pytest.raises(BaseData.BaseDataError):

        class Data(BaseData):
            x = "[mV]"
            y = "[m]"



def test_BaseData_3():
    # キーワード指定で逆に入れても問題ないか
    class Data(BaseData):
        x: "[mV]"
        y: "[m]"

    data = Data(y=10, x=19)
    assert data.x == 19
    assert data.y == 10


def test_BaseData_4():
    # アノテーションが空文字
    class Data(BaseData):
        x: ""

    assert Data.to_label() == "0:x"
    data = Data(x=1)
    assert data.x == 1


def test_BaseData_5():
    # コンストラクタを書いた場合はコンストラクタの制限がなくなる
    class Data(BaseData):
        x: "[mV]"
        y: "[m]"

        def __init__(self, x) -> None:
            self.x = 100
            super().__init__()

    data = Data(0)
    assert data.x == 100

def test_BaseData_6():
    # コンストラクタのエラー
    class Data(BaseData):
        value1: "[m]"
        value2: "[m]" 
    with pytest.raises(BaseData.BaseDataError):
        data=Data(1,1)

    with pytest.raises(BaseData.BaseDataError):
        data=Data(1)
    
    with pytest.raises(BaseData.BaseDataError):
        data=Data(value1=1)

    with pytest.raises(BaseData.BaseDataError):
        data=Data(value1=1,value2=1,value3=1)
        
    with pytest.raises(BaseData.BaseDataError):
        data=Data(value1=1,value3=1)
    
