import math
import statistics
import time
from collections import deque

from basedata import BaseData
from calibration import TMRCalibrationManager
from ExternalControl.GPIB.GPIB import (
    GPIBController,  # GPIBで接続する機器につながる# inst=GPIBController() でインスタンス作成 # inst.connect(<GPIBアドレス>)で接続 # inst.write(<コマンド>)でコマンド送信 # answer = inst.query(<コマンド>)でコマンド送信&読み取り
)
from ExternalControl.LinkamT95.Controller import (
    LinkamT95AutoController,  # リンカムの操作 # inst=LinkamT95AutoController() でインスタンス作成 # inst.connect(<COMPORTアドレス>)で接続(COMPORTアドレスはデバイスマネージャーからわかる) # inst.add_sequence(<コマンド>)でコマンド送信 # answer = inst.query(<コマンド>)でコマンド送信&読み取り
)
from filesplitter import FileSplitter
from measurement_manager import finish  # 測定の終了 引数なし
from measurement_manager import no_plot  # プロットしないときに使う
from measurement_manager import plot  # ウィンドウに点をプロット 引数は float,float
from measurement_manager import save  # ファイルに保存 引数はtuple
from measurement_manager import set_file  # ファイル名をセットする 引数はstring 引数なしだとダイアログを出す
from measurement_manager import set_label  # ファイルの先頭にラベル行をいれる
from measurement_manager import set_plot_info  # プロット情報入力
from measurement_manager import write_file  # ファイルへの書き込み引数は string
from split import TMR_split


#測定するデータの型とその単位を定義
class Data(BaseData):
    time:"[s]"
    frequency:"[Hz]"
    temperature:"[K]"
    capacitance:"[C]"
    permittivity_real:"" # 単位がないときは""をつける
    permittivity_image:""
    tan_delta:""
    resistance_Pt:"[Ohm]"
    heating_cooling:""


electrode_area:float #電極面積
depth:float #試料厚さ
start_time:float #測定開始時間
count=0 #今どの周波数で測定するのかを決める数字

ADRESS_LCR=7 #LCRのGPIB番号
ADRESS_Keithley=11 # Keithley2000のGPIB番号
COMPORT_LinkamT95="COM3" #Linkamのシリアルポート番号

#測定に使う機械はここで宣言しておく
LCR=GPIBController()
Keithley=GPIBController()
Linkam=LinkamT95AutoController()
calibration=TMRCalibrationManager()


e0= 8.8541878128*10**(-12)#真空の誘電率


def start():#最初に1回だけ実行される処理
    global electrode_area,depth,start_time #グローバル変数にはグローバル宣言をつける

    #機器に接続
    LCR.connect(ADRESS_LCR)
    Keithley.connect(ADRESS_Keithley)
    #Linkam.connect(COMPORT_LinkamT95) #シリアルポートのついてないLinkamもあったのでこのコマンドはコメントアウトしました

    set_file() #ファイル作成

    #電極面積, 試料の厚さを入力
    electrode_area=float(input("s[mm^2] is > ")) #電極面積入力
    depth=float(input("d[mm] is > ")) #試料の厚さ入力

    LCR.write("APER LONG") #測定モードをLONGに

    volt=LCR.query("VOLT?").replace(" ","") # LCRの電圧を取得
    label="s="+str(electrode_area)+"[mm2], d="+str(depth)+"[mm], V="+volt+"[V]"#ファイルの先頭につけるラベル
    
    set_label(label + "\n" + Data.to_label()) # ファイル先頭にラベルを付けておく
    calibration.set_shared_calib_file() #キャリブレーションの準備(shared_settings/calibration_fileフォルダから温度補正情報を取得)
    set_plot_info(line=False,xlog=False,ylog=False,renew_interval=1,flowwidth=0,legend=False) #プロット条件指定
    start_time=time.time()


    #Keithley2000の初期設定
    Keithley.write("SENS:FUNC 'FRES'") #四端子抵抗測定

    #Linkamに温度シーケンスを送信&実行 #シリアルポートのついてないLinkamがあったのでこのコマンドはコメントアウトしました
    # Linkam.add_sequence(T=300,hold=1,rate=10,lnp=1)
    # Linkam.add_sequence(T=30,hold=0,rate=10,lnp=-1)
    # Linkam.add_sequence(T=-70,hold=1,rate=10,lnp=-1)
    # Linkam.add_sequence(T=30,hold=0,rate=10,lnp=-1)
    # Linkam.add_sequence(T=300,hold=1,rate=10,lnp=1)
    # Linkam.add_sequence(T=30,hold=0,rate=10,lnp=1)
    # Linkam.start_sequence()


def update():#測定中に何度も実行される処理
    data=get_data()#データ取得
    if data.time>5*60*60: #5時間経ったら勝手に終了するように
        return False
    save(data)#セーブ
    plot(data.temperature,data.permittivity_real)#プロット


def get_data(): #実際に測定してる部分
    global count
    elapsed_time=time.time()-start_time

    frequency=pow(10,3+count*0.2)#周波数は10の(3+count*0.2)乗 (今回は3乗から6乗まで)
    LCR.write("FREQ "+str(frequency)) #周波数設定

    time.sleep(0.5)#0.5秒待つ

    lcr_ans=LCR.query("FETC?")#LCRのデータ読み取り(lcr_ansはコンマ区切りの文字列)
    array_string = lcr_ans.split(",")#コンマでわけて配列にする
    capacitance=float(array_string[0])#配列の0番目(今回は静電容量)を文字列から少数に
    tan_delta=float(array_string[1])#配列の1番目(今回はtanδ)を文字列から少数に

    
    permittivity_real=capacitance*depth/(electrode_area*e0)*1000#誘電率実部 (1000は単位合わせ)
    permittivity_image=permittivity_real*tan_delta#誘電率虚部

    
    resistnce=float(Keithley.query("FETCH?")) #プラチナ抵抗温度計の抵抗を取得
    temperature=temperature=calibration.calibration(resistnce) #抵抗値を温度に変換

    
  
    count=(count+1)%16 #countを1進める(16までいったら0に戻す)
    
    hc=heating_cooling_checker.check(elapsed_time,temperature) # heatingかcoolingかを判定
    #データに中身を入れて返す
    return Data(time=elapsed_time,frequency=frequency,temperature=temperature,capacitance=capacitance,permittivity_real=permittivity_real,permittivity_image=permittivity_image,tan_delta=tan_delta,resistance_Pt=resistnce,heating_cooling=hc)


def split(filepath):#測定ファイルを周波数分割
    FileSplitter(filepath=filepath,skip_rows=2,delimiter=",")\
        .column_value_split(colum_num=8,do_count=False,filename_formatter=None)\
        .column_value_split(colum_num=1,do_count=False,filename_formatter=lambda x : "1E{:.2f}Hz".format(math.log10(x)))\
        .create(delimiter="\t")


class HeatingCooligChecker:
    """温度変化をチェックするクラス"""
    TIME_INTERVAL=20 #20秒ごとにチェック(間隔が短すぎるとうまくいかない。長すぎると判定が遅れてしまう)
    T_SPEED_THREAHOLD=0.08 # [K/secound] を超えたら温度変化ありとする 今回は20秒で1.6℃変化する速度に対応
    def __init__(self) -> None:
        self.__step=0
        self.__pre_time=None
        self.__pre_temp=None
        self.__pre_judge="first"
    def check(self,time:float,temperature:float)->str:
        if self.__pre_time is None: #最初はpre_timeとpre_tempがNoneなのでそのまま値を入れる
            self.__pre_time=time
            self.__pre_temp=temperature


        judge=None
        if time - self.__pre_time > self.TIME_INTERVAL: # 前回からself.TIME_INTERVAL以上の時間が経過した場合
            T_speed=(temperature-self.__pre_temp)/(time-self.__pre_time) #温度変化速度を計算
            if abs(T_speed) > self.T_SPEED_THREAHOLD: #温度変化が一定以上なら judgeに値を入れる
                judge = f"{'heating' if T_speed > 0 else 'cooling'}"
                  
            self.__pre_time=time #新しい時間と温度の値を入れる
            self.__pre_temp=temperature
        
        if judge is not None: 
            if judge != self.__pre_judge: #前回とheating,coolingが変化していればstepを増やす
                self.__step +=1
        else:
            judge = self.__pre_judge #前回から時間が経過していない場合や温度変化がない場合には前回の値を入れる

        self.__pre_judge=judge 

        return f"{self.__step}_{judge}"

heating_cooling_checker=HeatingCooligChecker()