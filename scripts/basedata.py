"""



"""
from __future__ import annotations

import re
import textwrap
from typing import Any

from utility import MyException


class BaseData():
    """
    ユーザーマクロで使えるデータを保持するクラス
    利点としては
    1. 変数を定義するだけで変数を文字列にしてラベル化できる
        (クラス定義とラベル化を一箇所で行うので、変更のし忘れが発生しない)
    2. ラベル化の際に単位の情報も載せられる(単位はインスタンス変数と同名のクラス変数に格納)
    3. iterableなのでsave関数にそのまま渡せば展開される
    4. 自動的にdataclassになるので、コンストラクタが自動生成される
    """

    class BaseDataError(MyException):
        """データを保持するクラス関係のえらー"""

    def __setattr__(self, __name: str, __value: Any) -> None:
        """
        あとから要素を追加するのを阻止
        """
        
        if __name in self.__class__.__dict__.get("__annotations__").keys():
            super().__setattr__(__name,__value)
        else:
            raise self.BaseDataError(f"{__name}は{self.__class__.__name__}に最初に定義された変数に含まれていません。\n 使用する変数は宣言時に定義しておいてください")
    
    

    def __init_subclass__(cls,**kwargs) -> None:
        """
        このクラスを継承したクラスが作られたときに呼ばれる
        """
        attrs=cls.__dict__
        annotations=attrs.get("__annotations__") #型ヒントの付いた変数を取得
        #変数名を取得
        variables=dict(filter(lambda item: not re.fullmatch("__.*__",item[0]), cls.__dict__.items()))

        #全ての変数にアノテーションがついてなければエラー
        for v in variables.keys():
            if (annotations is None) or (v not in annotations.keys()):
                raise cls.BaseDataError(f'{cls.__name__}クラスの変数{v}の定義方法にエラーが発生しています. \n ' f'{cls.__base__.__name__}' 'を継承したクラスの変数は、{変数名}:"[{単位}]"の形にしてください \n 例) voltage:"[mV]"  \n     loopnumber:"" (単位がないときは "" をつける)')
        #アノテーションが文字列でなければエラー
        for var, anot in annotations.items():
            if type(anot) is not str:
                raise cls.BaseDataError(f'{cls.__name__}クラスの変数{var}の定義方法にエラーが発生しています. \n ' f'{cls.__base__.__name__}' 'を継承したクラスの変数は、{変数名}:"[{単位}]"の形にしてください \n 例) voltage:"[mV]"  \n     loopnumber:"" (単位がないときは "" をつける)')


        # コンストラクタが定義されてなければ自動的に定義
        if "__init__" not in cls.__dict__.keys():
            parameter_text=""
            assign_text=""
            default=False
            for parameter_name in annotations.keys():
                if cls.__dict__.get(parameter_name) is None:
                    parameter_text+=f"{parameter_name},"
                else:
                    raise cls.BaseDataError(f"{cls.__name__}クラスの変数定義の方法にエラーが存在します。\nBaseDataを継承したクラスではデフォルト値を設定することはできません。")

                assign_text+=f"self.{parameter_name}={parameter_name};"
            
            parameter_text=parameter_text[:-1]
            
            init_text=f"""
            def __init__(self,{parameter_text}):
                {assign_text}
                

            cls.__init__ = __init__

            """
            init_text=textwrap.dedent(init_text)
            exec(init_text) #文字列で書いたコードを実行


               
        
        return super().__init_subclass__(**kwargs) #これはおまじない


    @classmethod
    def to_label(cls):
        """
        ラベルデータの作成
        """
        
        annotations=cls.__dict__.get("__annotations__")
        text=""
        index=0
        for name,unit in annotations.items():
            text+=f"{index}:{name} {unit},  "
            index+=1
        text=text[:-3]
        return text


    def __iter__(self):
        """
        配列として扱えるようにするための関数
        """
        yield from  list(self.__dict__.values()) #変数をリストにして返す

    def __str__(self) -> str:
        return ",".join([str(s) for s in self.__dict__.values()])