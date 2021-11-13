import matplotlib.pyplot as plt
import time 
from multiprocessing import Process, Lock, Manager
import threading
import msvcrt
import sys
import numpy as np
import copy

"""
    プロットの処理と終了入力待ちは測定と別プロセスで行って非同期にする
    (データ数が増えてプロットに時間がかかっても測定に影響が出ないようにする)

"""




def exec(share_list,isfinish,lock,plot_info):#別プロセスで最初に実行される場所

    PlotWindow(share_list,isfinish,lock,**plot_info).run()#インスタンス作成, 実行

  


class PlotWindow():
    """

        測定データをグラフにするクラス

        Variables
        ____________
        share_list :List
            測定したデータを一時的に保管しておく場所
            非同期処理のため測定とプロットがずれるので, そのためにバッファーのようなものを挟む必要がある
            測定側で測定データをshare_listに詰めていく
            PlotWindowはshare_listのデータを取り込んでプロットした後に中身を消す
            この処理が衝突しないようにlock(セマフォ)をかけて排他制御する

        lock:
            プロセス間の共有ファイルを同時に触らないためのロック

        isfinish: 
            測定が終了した可動化を判定.
            測定が終了したらmeasurementManager側でisfinish=1が代入される


        
    """
   
    _figure=None
    _ax=None

    def __init__(self,share_list,isfinish,lock,xlog,ylog,renew_interval,flowwidth,line):#コンストラクタ
        self.share_list=share_list
        self.lock=lock
        self.interval=renew_interval
        self.flowwidth=flowwidth
        self.isfinish=isfinish
        self.linestyle=None if line else "None"

        #プロットウィンドウを表示
        plt.ion()#ここはコピペ
        self._figure, self._ax = plt.subplots(figsize=(8,6))#ここはコピペ
        if xlog:
            plt.xscale('log')#横軸をlogスケールに
        if ylog:
            plt.yscale('log')#縦軸をlogスケールに
    
    def run(self):#実行
        interval=self.interval
        while True:#一定時間ごとに更新
            self.renew_window()
            if self.isfinish.value==1:#終了していたらbreak
                break
            time.sleep(interval)

        while True:#終了してもグラフを表示したままにする
            try:
                self._figure.canvas.flush_events()
            except Exception:#｢ここでエラーが出る⇒グラフウィンドウを消した｣と想定してエラーはもみ消しループを抜ける
                break
            time.sleep(0.05)#グラフ操作のFPSを20くらいにする
   


        
    
    
    linedict={}
    max_x=None
    max_y=None
    min_x=None
    min_y=None
    def renew_window(self):#グラフの更新
        self.lock.acquire()#共有リストにロックをかける
        #share_listのコピーを作成.(temp=share_listにすると参照になってしまうのでdel self.share_list[:]でtempも消えてしまう)
        temp=self.share_list[:] #[i for i in self.share_list]はかなり重い
        del self.share_list[:]#共有リストは削除
        self.lock.release()#ロック解除


        relim=False

        for i in  range(len(temp)) :#tempの中身をプロット
            x,y,color=temp[i]

            if color not in self.linedict.keys():
                xarray=[x]
                yaaray=[y]
                ln,=self._ax.plot(xarray,yaaray,marker='.',color=color,linestyle=self.linestyle)
                lineobj=LineObj(ln,xarray,yaaray)
                self.linedict[color]=lineobj
            else:
                lineobj=self.linedict[color]
                lineobj.xarray.append(x)
                lineobj.yaaray.append(y)
                lineobj.ln.set_data(lineobj.xarray,lineobj.yaaray)

            
            if self.max_x is None:
                self.max_x=x
            elif self.max_x<x:
                self.max_x=x
                relim=True

            if self.max_y is None:
                self.max_y=y
            elif self.max_y<y:
                self.max_y=y
                relim=True    
            
            if self.min_x is None:
                self.min_x=x
            elif self.min_x>x:
                self.min_x=x
                relim=True

            if self.min_y is None:
                self.min_y=y
            elif self.min_y>y:
                self.min_y=y
                relim=True
        
        if relim:
            if self.flowwidth<=0:
                self._ax.set_xlim(self.min_x,self.max_x)
                self._ax.set_ylim(self.min_y,self.max_y)
            else:
                xmin=self.max_x-self.flowwidth
                self._ax.set_xlim(xmin,self.max_x)
                self._ax.set_ylim(self.min_y,self.max_y)

                for l in self.linedict.values():
                    xarray=l.xarray
                    yaaray=l.yaaray
                    cut=0
                    for i in range(len(xarray)):
                        if xarray[i]<xmin:
                            continue
                        else:
                            cut=max(i-1,0)
                            break
                    l.xarray=xarray[cut:]
                    l.yaaray=yaaray[cut:]

   
        self._figure.canvas.flush_events() #グラフを再描画するおまじない

class LineObj():

    def __init__(self,ln,xarray,yaaray):
        self.ln=ln
        self.xarray=xarray
        self.yaaray=yaaray
