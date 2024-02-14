import time

from instrument.GPIB import GPIBController, GPIBError
from measure.measurement import no_plot, print, save


def start():
    no_plot()


def update():
    print("今からSSRのテストを始めます...")
    time.sleep(1)

    print("まずGPIBの動作チェックをします...")
    while True:
        address = input("接続している機器のGPIB番号を入力してください >>")
        print("接続しています...")
        time.sleep(2)
        try:
            controller = GPIBController()
            controller.connect(int(address))
        except GPIBError as e:
            print("エラーが発生しました")
            print(f"エラーメッセージ: {e.message}")
            raise Exception(e.message)

        name = controller.query("*IDN?")
        print(f"接続している機器の名前は`{name}`です")

        print("GPIBのチェックを続けるならYを、そうでなければ別の文字を入力してください")
        if input() != "Y":
            break

    time.sleep(2)

    print("最後に、ファイル書き出しのチェックを行います")

    text = input("ファイルに書きたい文字を入力してください")

    save(text)

    return False


def after(path):
    print("終了しました。ファイルを確認してみてください")
    time.sleep(5)
