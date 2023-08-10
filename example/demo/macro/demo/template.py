import time

from measure.basedata import BaseData  # 測定データの基本クラス
from measure.measurement import plot  # ウィンドウに点をプロット 引数は float,float
from measure.measurement import print  # ターミナルへのログ出力
from measure.measurement import save  # ファイルに保存 引数はtuple
from measure.measurement import set_filename  # ファイル名をセットする 引数はstring 引数なしだとダイアログを出す
from measure.measurement import set_plot_info  # プロット情報入力


# 測定するデータとその単位を指定
class Data(BaseData):
    time: "[s]"
    capacitance: "[pC]"


# 最初に呼ばれる
def start():
    set_filename()

    # プロットする条件を指定、今回は点を線でつなぐように設定
    set_plot_info(line=True, xlog=False, ylog=False)

    # データ名と単位をファイル先頭に書き出す
    save(Data.to_label())

    print("スタート...")


count = 0


# 0から5までかぞえる
def update():
    # グローバル変数を使うときにはglobal宣言を行う
    global count

    print(f"{count}...")

    # 実際の測定の代わりにtimeとcapacitanceの値を入れる
    time_ = count
    capacitance_ = 100
    # データの作成
    data = Data(time=time_, capacitance=capacitance_)

    # プロット
    plot(data.time, data.capacitance)

    # 保存
    save(*data)

    count += 1
    if count == 5:
        # Falseを返すと測定が終了する
        return False

    time.sleep(1)


# 最後に呼ばれる
def end():
    print("end...")


# ファイルへの書き込みをすべて完了させてからよばれる ここではファイルに書き込みはできない
def after(path):
    print("after...")


# 測定中にコマンドを入力したら呼ばれる
def on_command(command):
    print(f"command is {command}")


# splitは周波数分割などをする際に用いる。これを書くと測定ファイルはフォルダに入れられる
# def split(path):
#    #分割用の処理をここに書く
