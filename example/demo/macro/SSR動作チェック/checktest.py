import time
from functools import cache

from ExternalControl.GPIB.GPIB import GPIBError, get_instrument
from measurement_manager import finish, no_plot, plot, save, set_plot_info, write_file


def start():
    no_plot()


def update():
    print("今からSSRのテストを始めます...")
    time.sleep(1)

    print("まずGPIBの動作チェックをします...")
    while True:

        num = input("接続している機器のGPIB番号を入力してください >>")
        print("接続しています...")
        time.sleep(2)
        try:
            inst = get_instrument(int(num))
        except GPIBError as e:
            print("エラーが発生しました")
            input(f"エラーメッセージ : {e.message}")
            raise Exception(e.message)

        name = inst.query("*IDN?")
        print(f"接続している機器の名前は {name} です")

        print("GPIBのチェックを続けるならYを、そうでなければ別の文字を入力してください\n")
        if input() != "Y":
            break

    time.sleep(2)

    print("最後に、ファイル書き出しのチェックを行います")

    text = input("ファイルに書きたい文字を入力してください")

    write_file(text)

    return False


def after(path):
    print("終了しました。ファイルを確認してみてください")
    time.sleep(5)
