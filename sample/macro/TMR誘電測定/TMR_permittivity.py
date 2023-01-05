import time

from basedata import BaseData
from calibration import TMRCalibrationManager
from GPIB import \
    GPIBController  # GPIBで接続する機器につながる# inst=GPIBController() でインスタンス作成 # inst.connect(<GPIBアドレス>)で接続 # inst.write(<コマンド>)でコマンド送信 # answer = inst.query(<コマンド>)でコマンド送信&読み取り
from LinkamT95.Controller import \
    LinkamT95AutoController  # リンカムの操作 # inst=LinkamT95AutoController() でインスタンス作成 # inst.connect(<COMPORTアドレス>)で接続(COMPORTアドレスはデバイスマネージャーからわかる) # inst.add_sequence(<コマンド>)でコマンド送信 # answer = inst.query(<コマンド>)でコマンド送信&読み取り
from measurement_manager import finish  # 測定の終了 引数なし
from measurement_manager import no_plot  # プロットしないときに使う
from measurement_manager import plot  # ウィンドウに点をプロット 引数は float,float
from measurement_manager import save  # ファイルに保存 引数はtuple
from measurement_manager import set_file_name  # ファイル名設定 引数は string
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

    filename=input("filename is >") #ファイル名の入力
    set_file_name(filename)


    #電極面積, 試料の厚さを入力
    electrode_area=float(input("s is > ")) #電極面積入力
    depth=float(input("d is > ")) #試料の厚さ入力

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
    

    #データに中身を入れて返す
    return Data(time=elapsed_time,frequency=frequency,temperature=temperature,capacitance=capacitance,permittivity_real=permittivity_real,permittivity_image=permittivity_image,tan_delta=tan_delta,resistance_Pt=resistnce)


def split(filepath):#測定ファイルを周波数分割
    TMR_split(filepath,T_index=2,f_index=1,freq_num=16,sample_and_cutout_num=(150,120),step=30)


