from __future__ import annotations

import copy
import math
import os
from pathlib import Path
from typing import List

import pandas as pd
from utility import MyException

"""
使用例

FileSplitter(filepath="all.txt",skip_rows=2,delimiter=",")\ #分割するファイルとスキップ行、区切り文字を設定
    .column_value_split(colum_num=8,filename_formatter=lambda x : f"{x}",do_count=True)\ #8行目(0始まり) の値で分割, カウントをつける
    .column_value_split(colum_num=9,filename_formatter=lambda x : "heating" if x>0 else "cooling",do_count=True)\#9行目(0始まり) の値で分割, カウントをつける
    .column_value_split(colum_num=1,filename_formatter=lambda x : "10E{:.2f}Hz".format(math.log10(x)),do_count=False)\ #1行目(0始まり) の値で分割, カウントをつけない
    .rename(filename_formatter=lambda data : f"{'heating' if data[9]>0 else 'cooling'}_{data[1]}Hz")\ # 2つ以上の列の値を使ってファイル名を作るときはrename関数を使う
    .create(delimiter="\t") #タブ区切りでファイル作成

"""


class FileSplitError(MyException):
    """ファイル分割関係のエラー"""


class FileSplitter:
    def __init__(self, filepath, skip_rows, delimiter) -> None:
        """
        FileSplitterのコンストラクタ

        Parameters
        --------------
        filepath: str
            分割するファイルのパス
        skip_rows: int
            読み飛ばす行数
        delimiter: str
            区切り文字
        """
        filepath = Path(filepath)
        with filepath.open(mode="r", encoding="utf-8") as f:
            self.label = ""
            for i in range(skip_rows):
                self.label += f.readline()
        data = pd.read_csv(
            filepath, skiprows=skip_rows, delimiter=delimiter, header=None
        )
        fileinfo = FileSplitter.FileInfo(
            name=filepath.stem, data=data.values.tolist(), count=None
        )
        fileinfo.is_root = True
        self.rootfileinfo = fileinfo
        self.folderpath = filepath.parent

    class FileInfo:
        def __init__(self, name, data, count) -> None:
            self.count = count
            self.name = name
            self.data = data
            self.children: List[FileSplitter.FileInfo] = []
            self.is_root = False

        def column_value_split(
            self, colum_num, filename_formatter, do_count
        ) -> FileSplitter:
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

            if len(self.children) > 0:  # 子供がいる場合は子供のcolumn_value_splitを実行して自身の分割は行わない
                for child in self.children:
                    child.column_value_split(colum_num, filename_formatter, do_count)
                return

            split_dic: dict[FileSplitter.FileInfo] = {}
            count = 0
            file_count = 0
            max_num = len(self.data)
            while True:
                row = self.data[count]  # count行目のデータを取得
                target_value = row[colum_num]  # count行目のデータからcolumn_num列目の値を取得
                if (
                    target_value in split_dic
                ):  # target_valueの値がsplit_dicにすでに存在しているならそこに振り分ける
                    split_dic[target_value].data.append(row)
                else:  # そうでない場合は新しくFileInfoを作ってdictに登録
                    # ファイル名を作成
                    if filename_formatter is None:
                        name = f"{target_value}"
                    else:
                        name = filename_formatter(target_value)

                    # 新しいFileInfo作成
                    new_fileinfo = FileSplitter.FileInfo(
                        name=name, data=[], count=file_count if do_count else None
                    )
                    new_fileinfo.data.append(row)
                    split_dic[target_value] = new_fileinfo  # 辞書にFileInfo追加
                    file_count += 1
                count += 1
                if count >= max_num:
                    break

            # 辞書に登録したFileInfoをchildrenに追加
            for f in split_dic.values():
                self.children.append(f)

        def create(self, folder_path: Path, delimiter, label):
            """
            ファイル作成
            子供がいる場合には子供のcreateを作動させて連鎖的にファイルを作成する

            Parameters
            ----------
            delimiter : str
                出力ファイルの区切り文字
            """
            if not self.is_root:  # rootFile(分割元ファイル)以外ならファイル作成
                file_name = (
                    f"{self.count}_" if self.count is not None else ""
                ) + self.name  # ファイル名
                if len(self.children) > 0:  # childrenがいるならフォルダを作成
                    folder_path = folder_path / file_name
                    path = folder_path / ("_" + file_name + ".txt")
                else:  # childrenがいないならフォルダを作成せず、親と同じフォルダにファイルを作成
                    path = folder_path / (file_name + ".txt")
                path.parent.mkdir(parents=True, exist_ok=True)

                # データの書き込み
                with path.open(mode="x", encoding="utf-8") as f:
                    f.write(label)
                    for d in self.data:
                        f.write(delimiter.join([str(dd) for dd in d]) + "\n")

            # childrenがいるなら子供のFileInfoのcreate関数を実行
            if len(self.children) > 0:
                for child in self.children:
                    child.create(
                        folder_path=folder_path, delimiter=delimiter, label=label
                    )

        def rename(self, filename_formatter):
            """
            ファイル名を変更する
            変更するのは末端のファイル(子供のいないファイル)のみ

            Parameters
            ----------------
            filename_formatter : ファイル名を決める関数 引数は1行目のデータ配列
            """
            if (not self.is_root) and len(
                self.children
            ) == 0:  # 分割元ファイルでなく、childrenのいないFileInfo(末端のFileInfo)ならrename
                data = self.data[0]
                self.name = filename_formatter(data)

            if len(self.children) > 0:  # childrenがいれば子供のFileInfoのrenemeを実行
                for child in self.children:
                    child.rename(filename_formatter=filename_formatter)

        def get_file_num(self):
            """ファイル数を数える"""
            count = 1
            if len(self.children) > 0:
                for child in self.children:
                    count += child.get_file_num()
            return count

    def column_value_split(
        self, colum_num, filename_formatter=None, do_count=False
    ) -> FileSplitter:
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
        self.rootfileinfo.column_value_split(
            colum_num=colum_num,
            filename_formatter=filename_formatter,
            do_count=do_count,
        )
        return self

    def create(self, delimiter=",", do_limit_filenum=True):
        """
        ファイル作成 FileSplitterは最後にこれを呼ばないとファイル作成をしない

        Parameters
        ----------
        delimiter : str
            出力ファイルの区切り文字
        do_limit_filenum : bool
            分割数に上限をつける (間違えた分割をした際に大量のファイルを作成しないようにするため)
        """
        if do_limit_filenum:
            if self.rootfileinfo.get_file_num() > 500:
                raise (
                    FileSplitError(
                        "分割後のファイルの数が500を超えています.どうしても分割したい場合はdo_limit_filenum=Trueにしてください"
                    )
                )
        self.rootfileinfo.create(self.folderpath, delimiter=delimiter, label=self.label)

    def rename(self, filename_formatter):
        """
        ファイル名を変更する
        変更するのは末端のファイルのみ

        Parameters
        ----------------
        filename_formatter : ファイル名を決める関数 引数は1行目のデータ配列
        """
        self.rootfileinfo.rename(filename_formatter=filename_formatter)
        return self
