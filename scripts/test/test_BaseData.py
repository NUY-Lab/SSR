import sys
import unittest

sys.path.append("../")

from basedata import BaseData


class TestLinkamT95IO(unittest.TestCase):
    def test1(self):
        class Data(BaseData):
            x: "[mV]"
            y: "[m]"

        data = Data(1, 2)
        self.assertEqual(data.x, 1)
        self.assertEqual(data.y, 2)
        data.x = 0
        self.assertEqual(data.x, 0)
        self.assertEqual(list(data), [0, 2])
        self.assertEqual(Data.to_label(), "0:x [mV],  1:y [m]")

        with self.assertRaises(BaseData.BaseDataError):
            data.z = 100  # 存在しない属性に代入

    def test2(self):
        # 不正な型定義
        with self.assertRaises(BaseData.BaseDataError):

            class Data(BaseData):
                x: "[mV]"
                y: "[mV]" = 10

        with self.assertRaises(BaseData.BaseDataError):

            class Data(BaseData):
                x: "[mV]"
                y: int

        with self.assertRaises(BaseData.BaseDataError):

            class Data(BaseData):
                x = 10
                y = None

        with self.assertRaises(BaseData.BaseDataError):

            class Data(BaseData):
                x = "[mV]"
                y = "[m]"

    def test3(self):
        # キーワード指定で逆に入れても問題ないか
        class Data(BaseData):
            x: "[mV]"
            y: "[m]" = 2

        data = Data(y=10, x=19)
        self.assertEqual(data.x, 19)
        self.assertEqual(data.y, 10)

    def test3(self):
        # アノテーションが空文字
        class Data(BaseData):
            x: ""

        self.assertEqual(Data.to_label(), "0:x ")
        data = Data(1)
        self.assertEqual(data.x, 1)

    def test4(self):
        # コンストラクタを書いた場合
        class Data(BaseData):
            x: "[mV]"
            y: "[m]"

            def __init__(self, x) -> None:
                self.x = 100
                super().__init__()

        data = Data(0)
        self.assertEqual(data.x, 100)
