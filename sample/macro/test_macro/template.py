import time

# GPIBで接続する機器につながる
# inst=GPIBController() でインスタンス作成
# inst.connect(<GPIBアドレス>)で接続
# inst.write(<コマンド>)でコマンド送信
# answer = inst.query(<コマンド>)でコマンド送信&読み取り
from instrument.GPIB import GPIBController

# リンカムの操作
# inst=LinkamT95AutoController()でインスタンス作成
# inst.connect(<COMPORTアドレス>)で接続(COMPORTアドレスはデバイスマネージャーからわかる)
# inst.add_sequence(<コマンド>)でコマンド送信
# answer = inst.query(<コマンド>)でコマンド送信&読み取り
from instrument.LinkamT95 import LinkamT95AutoController
from measure.basedata import BaseData  # 測定データの基本クラス
from measure.masurement import finish  # 測定の終了 引数なし
from measure.masurement import log  # ターミナルへのログ出力
from measure.masurement import no_plot  # プロットしないときに使う
from measure.masurement import plot  # ウィンドウに点をプロット 引数は float,float
from measure.masurement import save  # ファイルに保存 引数はtuple
from measure.masurement import set_file  # ファイル名をセットする 引数はstring 引数なしだとダイアログを出す
from measure.masurement import set_label  # ファイルの先頭にラベル行をいれる
from measure.masurement import set_plot_info  # プロット情報入力
from measure.masurement import write_file  # ファイルへの書き込み引数は string


# 測定するデータとその単位を指定
class Data(BaseData):
    time: "[s]"
    capacitance: "[pC]"


# 最初に呼ばれる
def start():
    set_file()

    # プロットする条件を指定、今回は点を線でつなぐように設定
    set_plot_info(line=True, xlog=False, ylog=False)

    # データ名と単位をファイル先頭に書き出す
    set_label(Data.to_label())

    log("スタート...")


count = 0


# 0から5までかぞえる
def update():
    # グローバル変数を使うときにはglobal宣言を行う
    global count

    log(f"{count}...")

    # 実際の測定の代わりにtimeとcapacitanceの値を入れる
    time_ = count
    capacitance_ = 100
    # データの作成
    data = Data(time=time_, capacitance=capacitance_)

    # プロット
    plot(data.time, data.capacitance)

    # 保存
    save(data)

    count += 1
    if count == 5:
        # Falseを返すと測定が終了する
        return False

    time.sleep(1)


# 最後に呼ばれる
def end():
    log("end...")


# ファイルへの書き込みをすべて完了させてからよばれる ここではファイルに書き込みはできない
def after(path):
    log("after...")


# 測定中にコマンドを入力したら呼ばれる
def on_command(command):
    log(f"command is {command}")


# splitは周波数分割などをする際に用いる。これを書くと測定ファイルはフォルダに入れられる
# def split(path):
#    #分割用の処理をここに書く
