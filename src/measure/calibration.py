"""キャリブレーションに使う関数"""
import os
from logging import getLogger
from pathlib import Path
from typing import Callable

from scipy import interpolate

from .error import SSRError
from .util import get_encode_type
from .variable import SHAREDDIR

logger = getLogger(__name__)


class CalibrationError(SSRError):
    """キャリブレーション関連のエラー"""


class TMRCalibrationManager:
    """TMRの温度校正を行う

    Variables
    ---------
    calib_file_name:
        キャリブレーションファイルの名前

    Methods
    -------
    set_shared_calib_file():
        SHARED_SETTINGSフォルダに入ったキャリブレーションファイルを使って温度校正を行います
    set_own_calib_file(filepath_calib: str):
        キャリブレーションを指定して温度校正を行います。普通は使いません。
    calibration(x: float): float
        入力xに対して線形補間を行ったyを返します
    """

    calib_file_name: str
    interpolate_func: Callable[[float], float] | None = None

    def set_shared_calib_file(self) -> None:
        """キャリブレーションファイルを共有フォルダから取得してインスタンスにセット"""
        path = SHAREDDIR / "calibration_file"
        if not path.is_dir():
            path.mkdir()
        import glob

        files = glob.glob(str(path) + "/*")
        # 名前の先頭にアンダーバーがあるものは排除
        files = list(filter(lambda f: os.path.split(f)[1][0] != "_", files))

        if len(files) == 0:
            raise CalibrationError(f"{str(path)}内には1つのキャリブレーションファイルを置く必要があります")
        if len(files) >= 2:
            raise CalibrationError(
                f"{str(path)}内に2つ以上のキャリブレーションファイルを置いてはいけません。"
                "古いファイルの先頭にはアンダーバー'_'をつけてください"
            )
        filepath_calib = files[0]
        self.__set(Path(filepath_calib))

    def set_own_calib_file(self, filepath_calib: str) -> None:
        """自分で指定したキャリブレーションファイルをインスタンスにセット"""
        path = Path(filepath_calib)
        if not path.is_file():
            raise CalibrationError(
                f"キャリブレーションファイル{filepath_calib}が存在しません. "
                f"{os.getcwd()}で'{filepath_calib}'にアクセスしようとしましたが存在しませんでした."
            )
        self.__set(path)

    def __set(self, filepath_calib: Path) -> None:
        """プラチナ温度計の抵抗値を温度に変換するためのファイルを読み込み
        キャリブレーションファイルの2列目をx,1列目をyとして線形補間関数を作る.

        Parameter
        ---------

        filepath_cali: Path
            キャリブレーションファイルのパス.
        """

        if not filepath_calib.is_file():
            raise CalibrationError(
                f"キャリブレーションファイル{str(filepath_calib)}が存在しません. "
                f"{os.getcwd()}で'{str(filepath_calib)}'にアクセスしようとしましたが存在しませんでした."
            )

        with filepath_calib.open(encoding=get_encode_type(filepath_calib)) as file:
            x = []
            y = []

            for line in file:
                line = line.strip()

                # 空なら終了
                if line == "":
                    break

                try:
                    # ","で分割して配列にする
                    # 文字列からfloatに変換
                    array_float = [float(s) for s in line.split(",")]

                    x.append(array_float[1])  # 抵抗値の情報
                    y.append(array_float[0])  # 対応する温度の情報
                except Exception:
                    pass

        self.calib_file_name = filepath_calib.parts[1]
        logger.info(f"calibration: {str(filepath_calib)}")

        # 線形補間関数定義
        self.interpolate_func = interpolate.interp1d(
            x, y, bounds_error=False, fill_value="extrapolate"
        )

    def calibration(self, x: float) -> float:
        """プラチナ温度計の抵抗値xに対応する温度yを線形補間で返す"""
        try:
            y = self.interpolate_func(x)
        except ValueError as e:
            raise CalibrationError(
                f"入力されたデータ{str(x)}がキャリブレーションファイルのデータ範囲外になっている可能性があります"
            ) from e
        except NameError as e:
            raise CalibrationError("キャリブレーションファイルが読み込まれていない可能性があります") from e
        except Exception as e:
            raise CalibrationError("予期せぬエラーが発生しました") from e
        return y
