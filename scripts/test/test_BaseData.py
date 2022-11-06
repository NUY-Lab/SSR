import sys
import unittest

sys.path.append("../")

from basedata import BaseData


class TestLinkamT95IO(unittest.TestCase):

    def test1(self):
        class Data(BaseData):
            x:int="[mV]"
            y:int="[m]"

        data=Data(1,2)
        self.assertEqual(data.x,1)
        self.assertEqual(data.y,2)
        data.x=0
        self.assertEqual(data.x,0)
        self.assertEqual(list(data),[0,2])
        self.assertEqual(Data.to_label(),"0:x[mV],  1:y[m]")

        with self.assertRaises(BaseData.BaseDataError):
            data.z=100 #存在しない属性に代入

    def test2(self):
        with self.assertRaises(BaseData.BaseDataError):
            class Data(BaseData):
                x:int="[mV]"
                y:int
        with self.assertRaises(BaseData.BaseDataError):
            class Data(BaseData):
                x="[mV]"
                y="[m]"

            data=Data(1,2)
        