import time
from functools import cache

from ExternalControl.GPIB.GPIB import GPIBError, get_instrument
from measurement_manager import finish, no_plot, plot, save, set_plot_info, write_file


def start():
    no_plot()


def update():
    print("今からコマンドのテストを始めます...")
    time.sleep(1)
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

    
    while True:
        print("機器におくるコマンドを入力してください... 終了する際はウィンドウを閉じてください\n")
        command= input()
        if command == "":
            continue

        try:
            ans=inst.query(command)
            print(f"返り値 >> {ans}\n")
        except:
            print("返り値はありません\n")
        
        

