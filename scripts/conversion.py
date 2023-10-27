"""
x-yのデータ表をもとに変換グラフを作って

新しいxのデータを変換表に合わせて変換する
"""

from logging import getLogger

import numpy as np
from scipy import interpolate
from utility import MyException, get_encode_type

logger = getLogger(f"SSR.{__name__}")

class ConverterError(MyException):
    """データ変換関連のエラー"""

class DataConverter:

    _interpolate_func=None
    def set_file(self,filepath,skiprows,delimiter):
        """データ変換に使う変換表をセット(ファイルから)"""
        datas = np.loadtxt(fname=filepath,skiprows=skiprows,delimiter=delimiter,unpack=True,encoding=get_encode_type(filepath))
        self.set_table(datas[0],datas[1])
    def set_table(self,x,y,bounds_error=False, fill_value="extrapolate"):
        """データ変換に使う変換表をセット(x,yの配列から)"""
        self._interpolate_func = interpolate.interp1d(
            x, y, bounds_error=bounds_error, fill_value=fill_value
        )  # 線形補間関数定義
    def convert(self,input_value):
        """データ変換表に合わせて入力データを変換"""
        try:
            output_value = self._interpolate_func(input_value)
        except ValueError as e:
            raise ConverterError(
                "入力されたデータ " + str(input_value) + " がデータ変換の範囲外になっている可能性があります"
            ) from e
        except NameError as e:
            raise ConverterError("データ変換表ファイルが読み込まれていない可能性があります") from e
        except Exception as e:
            raise ConverterError("予期せぬエラーが発生しました") from e
        return output_value

    