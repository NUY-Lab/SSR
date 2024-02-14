import math
import time

# GPIBで接続する機器につながる
# inst=GPIBController() でインスタンス作成
# inst.connect(<GPIBアドレス>)で接続
# inst.write(<コマンド>)でコマンド送信
# answer = inst.query(<コマンド>)でコマンド送信&読み取り
from instrument.GPIB import GPIBController

# 簡易的なファイル分割ができる関数
from macro.util.split import TMR_split
from measure.basedata import BaseData
from measure.calibration import TMRCalibrationManager
from measure.measurement import finish, plot, save, set_filename, set_plot_info

# from filesplitter import FileSplitter
# from measurement_manager import finish  # 測定の終了 引数なし
# from measurement_manager import no_plot  # プロットしないときに使う(高速化するときなど)
# from measurement_manager import plot  # ウィンドウに点をプロット 引数は float(X座標),float(Y座標)
# from measurement_manager import save  # ファイルに保存 引数はtupleもしくはDataクラスの変数
# from measurement_manager import set_file  # ファイル名をセットする 引数はstring 引数なしだとファイル保存ダイアログを出す
# from measurement_manager import set_header  # ファイルの先頭にラベル行をいれる
# from measurement_manager import set_plot_info  # プロット情報入力 (対数軸にするかなど)
# from measurement_manager import write_file  # ファイルへの書き込み 引数はstring (save関数と似てる)


# 測定するデータの型とその単位を定義
class Data(BaseData):
    time: "[s]"
    frequency: "[Hz]"
    temperature: "[K]"
    capacitance: "[F]"
    permittivity_real: ""  # 単位がないときは""をつける
    permittivity_image: ""
    tan_delta: ""
    resistance_Pt: "[Ohm]"
    heating_cooling: ""


electrode_area: float  # 電極面積
depth: float  # 試料厚さ
start_time: float  # 測定開始時間
count = 0  # 今どの周波数で測定するのかを決める数字

# LCR,Keithley2000のGPIB番号
ADRESS_LCR = 7
ADRESS_Keithley = 11

# 測定に使う機械はここで宣言しておく
LCR = GPIBController()
Keithley = GPIBController()
calibration = TMRCalibrationManager()


# 真空の誘電率
e0 = 8.8541878128e-12


# 最初に1回だけ実行される処理
def start():
    # グローバル変数にはグローバル宣言をつける
    global electrode_area, depth, start_time

    # 機器に接続
    LCR.connect(ADRESS_LCR)
    Keithley.connect(ADRESS_Keithley)

    # ファイル作成
    set_filename()

    # 電極面積, 試料の厚さを入力
    electrode_area = float(input("s[mm^2] is > "))
    depth = float(input("d[mm] is > "))

    LCR.write("APER LONG")  # 測定モードをLONGに
    LCR.write("FUNC:IMP:TYPE CPD")  # Cp-Dの測定モードに

    volt = LCR.query("VOLT?").replace(" ", "")  # LCRの電圧を取得

    # ファイル先頭にラベルを付けておく
    save(f"s={electrode_area}[mm2]", f"d={depth}[mm]", f"V={volt}[V]")
    save(Data.to_label())

    # キャリブレーションの準備(shared_settings/calibration_fileフォルダから温度補正情報を取得)
    calibration.set_shared_calib_file()
    # プロット条件指定
    set_plot_info()

    # スタート時刻を取得
    start_time = time.time()

    # Keithley2000の初期設定
    # 四端子抵抗測定
    Keithley.write("SENS:FUNC 'FRES'")


# 測定中に何度も実行される処理
# Falseを返すと終了する. それ以外のときはupdateを繰り返し続ける
def update():
    data = get_data()

    # 5時間経ったら勝手に終了する
    if data.time > 5 * 60 * 60:
        return False

    # 測定データを保存
    save(data)

    # プロット labelに値を入れることで色分けできる
    plot(data.temperature, data.permittivity_real, label=count)


# 実際に測定してる部分
def get_data():
    global count

    elapsed_time = time.time() - start_time

    # 周波数設定
    # 周波数は10の(3+count*0.2)乗 (今回は3乗から6乗まで)
    frequency = pow(10, 3 + count * 0.2)
    LCR.write(f"FREQ {frequency}")

    time.sleep(0.5)

    # LCRのデータ読み取り(lcr_ansはコンマ区切りの文字列)
    lcr_ans = LCR.query("FETC?")
    # コンマでわけて配列にする
    array_string = lcr_ans.split(",")
    # 配列の0番目(今回は静電容量)と1番目(今回はtanδ)を文字列から少数に
    capacitance = float(array_string[0])
    tan_delta = float(array_string[1])

    # 誘電率実部(1000は単位合わせ)と誘電率虚部
    permittivity_real = capacitance * depth / (electrode_area * e0) * 1000
    permittivity_image = permittivity_real * tan_delta

    # プラチナ抵抗温度計の抵抗を取得して抵抗値を温度に変換
    resistnce = float(Keithley.query("FETCH?"))
    temperature = calibration.calibration(resistnce)

    # countを1進める(16までいったら0に戻す)
    count = (count + 1) % 16

    # heatingかcoolingかを判定
    hc = heating_cooling_checker.check(elapsed_time, temperature)

    # データに中身を入れて返す
    return Data(
        time=elapsed_time,
        frequency=frequency,
        temperature=temperature,
        capacitance=capacitance,
        permittivity_real=permittivity_real,
        permittivity_image=permittivity_image,
        tan_delta=tan_delta,
        resistance_Pt=resistnce,
        heating_cooling=hc,
    )


# 測定ファイルを周波数分割
def split(filepath):
    # 1行目はファイル読み込み. skip_rowsは読み飛ばしの行数, delimiterは区切り文字(タブなら"\t") \は改行記号
    # 2,3行目はファイル分割. colum_numは分割に使う列,指定した列の値ごとにファイルを分割する. do_countで番号つけてfilename_formatterでファイル名を整形する
    # 4行目はファイル作成
    FileSplitter(
        filepath=filepath,
        skip_rows=2,
        delimiter="\t",
    ).column_value_split(
        colum_num=8,
        do_count=False,
        filename_formatter=None,
    ).column_value_split(
        colum_num=1,
        do_count=False,
        filename_formatter=lambda x: "1E{:.2f}Hz".format(math.log10(x)),
    ).create(
        delimiter="\t"
    )


class HeatingCooligChecker:
    """
    温度変化をチェックするクラス
    温度変化判定プログラムの設計上、温度変化直後の時間は判定できないのでデータが切れてしまう。
    それが嫌な人は別の判定プログラムを作ってください
    (例えば、このプログラムではheating → coolingの変化を検知したときに heating,coolingを変えるが、
    温度変化が止まった時点でheatingとcoolingを変えることでデータを切ることなく判定できる。そのかわりプログラムの柔軟性は落ちる。)
    """

    # 20秒ごとにチェック(間隔が短すぎるとうまくいかない。長すぎると判定が遅れてしまう)
    TIME_INTERVAL = 20
    # [K/second] を超えたら温度変化ありとする 今回は20秒で1.6℃変化する速度に対応
    T_SPEED_THREAHOLD = 0.08

    def __init__(self) -> None:
        self._step = 0
        self._pre_time = None
        self._pre_temp = None
        self._pre_judge = "first"

    def check(self, time: float, temperature: float) -> str:
        """温度変化判定"""

        # 最初はpre_timeとpre_tempがNoneなのでそのまま値を入れる
        if self._pre_time is None:
            self._pre_time = time
            self._pre_temp = temperature

        judge = self._pre_judge

        # 前回からself.TIME_INTERVAL以上の時間が経過した場合
        if time - self._pre_time > self.TIME_INTERVAL:
            # 温度変化速度
            T_speed = (temperature - self._pre_temp) / (time - self._pre_time)

            # 温度変化が一定以上なら judgeに値を入れる
            if abs(T_speed) > self.T_SPEED_THREAHOLD:
                judge = f"{'heating' if T_speed > 0 else 'cooling'}"

                # 前回とheating,coolingが変化していればstepを増やす
                if judge != self._pre_judge:
                    self._step += 1
                    self._pre_judge = judge

            # 時間と温度を更新
            self._pre_time = time
            self._pre_temp = temperature

        return f"{self._step}_{judge}"


heating_cooling_checker = HeatingCooligChecker()
