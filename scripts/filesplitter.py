from __future__ import annotations

import copy
import math
import os
from pathlib import Path
from typing import List

import pandas as pd

"""
使用例

FileSplitter(filepath="all.txt",skip_rows=2,delimiter=",")\ #分割するファイルとスキップ行、区切り文字を設定
    .column_value_split(colum_num=8,filename_formatter=lambda x : f"{x}",do_count=True)\ #8行目(0始まり) の値で分割, カウントをつける
    .column_value_split(colum_num=9,filename_formatter=lambda x : "heating" if x>0 else "cooling",do_count=True)\#9行目(0始まり) の値で分割, カウントをつける
    .column_value_split(colum_num=1,filename_formatter=lambda x : "10E{:.2f}Hz".format(math.log10(x)),do_count=False)\ #1行目(0始まり) の値で分割, カウントをつけない
    .rename(filename_formatter=lambda data : f"{'heating' if data[9]>0 else 'cooling'}_{data[1]}Hz")\ # 2つ以上の列の値を使ってファイル名を作るときはrename関数を使う
    .create(delimiter="\t") #タブ区切りでファイル作成

"""

class FileSplitter:

    
    class FileInfo:
        def __init__(self,name,data,count) -> None:
            self.count=count
            self.name=name
            self.data=data
            self.children:List[FileSplitter.FileInfo]=[]
            self.is_root=False

        def column_value_split(self,colum_num,filename_formatter,do_count) ->FileSplitter:
            """列の値で分割

            Parameters
            ----------

            colum_num: int
                参照する列の番号(0始まり)

            do_count : bool
                ファイル名の先頭に番号をつけるかどうか

            
            filename_formatter :ラムダ式
                colum_numの列の値からファイル名を作成する関数

            """

            if len(self.children)>0: #子供がいる場合は子供のcolumn_value_splitを実行して自身の分割は行わない
                for child in self.children:
                    child.column_value_split(colum_num,filename_formatter,do_count)
                return
                
            
            new_fileinfo_list:List[FileSplitter.FileInfo]=[]
            

            split_dic:dict[FileSplitter.FileInfo] ={}
            count=0
            file_count=0
            max_num=len(self.data)
            while True:
                row=self.data[count]
                target_value=row[colum_num]
                if target_value in split_dic:
                    split_dic[target_value].data.append(row)
                else:
                    if filename_formatter is None:
                        name= f"{target_value}"
                    else:
                        name=filename_formatter(target_value)
                    

                    new_fileinfo=FileSplitter.FileInfo(
                        name=name,
                        data=[],
                        count= file_count if do_count else None
                        )
                    new_fileinfo.data.append(row)
                    split_dic[target_value]=new_fileinfo
                    file_count+=1
                count+=1
                if count >= max_num:
                    break
            
            for f in split_dic.values():
                new_fileinfo_list.append(f)


            for nf in new_fileinfo_list:
                self.children.append(nf)
            
        def create(self,folder_path:Path,delimiter,label):
            """
            ファイル作成
            子供がいる場合には子供のcreateを作動させて連鎖的にファイルを作成する

            Parameters
            ----------
            delimiter : str
                出力ファイルの区切り文字
            """
            if not self.is_root:
                file_name=(f"{self.count}_" if self.count is not None else "") +self.name
                if len(self.children)>0:
                    folder_path=folder_path/file_name
                    path=folder_path / ("_"+file_name+".txt")
                else:
                    path=folder_path/ (file_name+".txt")
                
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open(mode="x",encoding="utf-8") as f:
                    f.write(label)
                    for d in self.data:
                        f.write(delimiter.join([str(dd) for dd in d])+"\n")

            if len(self.children)>0:
                for child in self.children:
                    child.create(folder_path=folder_path,delimiter=delimiter,label=label)
        
        def rename(self,filename_formatter):
            """
            ファイル名を変更する
            変更するのは末端のファイル(子供のいないファイル)のみ

            Parameters
            ----------------
            filename_formatter : ファイル名を決める関数 引数は1行目のデータ配列
            """
            if (not self.is_root) and len(self.children)==0:
                data=self.data[0]
                self.name=filename_formatter(data)

            if len(self.children)>0:
                for child in self.children:
                    child.rename(filename_formatter=filename_formatter)


                

        
        
        

    def __init__(self,filepath,skip_rows,delimiter) -> None:
        filepath=Path(filepath)
        with filepath.open(mode="r",encoding="utf-8") as f:
            self.label=""
            for i in range(skip_rows):
                self.label+=f.readline()
        data=pd.read_csv(filepath,skiprows=skip_rows,delimiter=delimiter,header=None)
        fileinfo=FileSplitter.FileInfo(name=filepath.stem,data=data.values.tolist(),count=None)
        fileinfo.is_root=True
        self.rootfileinfo=fileinfo
        self.folderpath=filepath.parent
    
    def column_value_split(self,colum_num,filename_formatter=None,do_count=False) ->FileSplitter:
        """列の値で分割

            Parameters
            ----------

            colum_num: int
                参照する列の番号(0始まり)

            do_count : bool
                ファイル名の先頭に番号をつけるかどうか

            
            filename_formatter :ラムダ式
                colum_numの列の値からファイル名を作成する関数
                デフォルトではcolum_numの列の値がそのままファイル名になる

            """
        self.rootfileinfo.column_value_split(colum_num=colum_num,filename_formatter=filename_formatter,do_count=do_count)
        return self
    
    
    
    def create(self,delimiter=","):
        """
        ファイル作成 FileSplitterは最後にこれを呼ばないとファイル作成をしない

        Parameters
        ----------
        delimiter : str
            出力ファイルの区切り文字
        """
        self.rootfileinfo.create(self.folderpath,delimiter=delimiter,label=self.label)

    def rename(self,filename_formatter):
        """
            ファイル名を変更する
            変更するのは末端のファイルのみ

            Parameters
            ----------------
            filename_formatter : ファイル名を決める関数 引数は1行目のデータ配列
        """
        self.rootfileinfo.rename(filename_formatter=filename_formatter)
        return self




# FileSplitter(filepath="./test/all.txt",delimiter=",",skip_rows=2)\
#     .column_value_split(colum_num=8,filename_formatter=Formatter_Factory_Light())\
#         .column_value_split(colum_num=9,filename_formatter=Formatter_Factory_Heat())\
#             .column_value_split(colum_num=1,filename_formatter=lambda x : "10E{:.2f}Hz".format(math.log10(x)))\
#                 .create(delimiter="\t")
