import time

from GPIB import get_instrument
from measurement_manager import finish  # 測定の終了 引数なし
from measurement_manager import plot  # ウィンドウに点をプロット 引数は float,float
from measurement_manager import save  # ファイルに保存 引数はtuple
from measurement_manager import set_file_name  # ファイル名設定 引数は string
from measurement_manager import set_plot_info  # プロット情報入力
from measurement_manager import write_file  # ファイルへの書き込み引数は string
from measurement_manager import no_plot


def start():  # 最初に呼ばれる
    set_file_name("テスト用ファイル")
    print("スタート...")


count = 0
number = 10

# 0から5まで
def update():
    global count

    print(f"{count}...")

    plot(count, number)
    save(count, number)

    count += 1
    if count == 5:
        return False  # Falseを返すと測定が終了する

    time.sleep(1)  # 1秒待機


def end():  # 最後に呼ばれる
    print("end...")


def after(path):  # ファイルへの書き込みをすべて完了させてからよばれる ここではファイルに書き込みはできない
    print("after...")


def on_command(command):  # 測定中にコマンドを入力したら呼ばれる
    print(f"command is {command}")


# splitは周波数分割などをする際に用いる。これを書くと測定ファイルはフォルダに入れられる
# def split(path):
#    #分割用の処理をここに書く
