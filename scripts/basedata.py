"""



"""
from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass, is_dataclass
from typing import Any, Callable

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
        if hasattr(self,__name):
            super().__setattr__(__name,__value)
        else:
            raise self.BaseDataError(f"{__name}は{self.__class__.__name__}に最初に定義された変数に含まれていません。\n 使用する変数は宣言時に定義しておいてください")
    
    

    def __init_subclass__(cls,**kwargs) -> None:
        """
        このクラスを継承したクラスが作られたときに呼ばれる
        """
        attrs=cls.__dict__
        annotations=attrs.get("__annotations__") #フィールド名？を取得
        if annotations is not None:
            for field_name in annotations.keys():
                unit_str=attrs.get(field_name) # クラス変数に入っているはずの単位情報を取得
                if type(unit_str) is not str: #単位情報がない or 文字列でないときはエラー         
                    raise cls.BaseDataError(f'{cls.__name__}クラスの定義方法にエラーが発生しています. \n ' f'{cls.__base__.__name__}' 'を継承したクラスの変数は、{変数名}:{データ型(わからなければfloat)} ="[{単位}]"の形にしてください \n 例) voltage:float = "[mV]"  \n     loopnumber:int = "" (単位がないときは "" をつける)')
                
        dataclass(cls) #強制的にdataclassにする
        cls.__init__.__defaults__=() #クラス変数がコンストラクタのデフォルトの値になっているので削除しておく
        return super().__init_subclass__(**kwargs) #これはおまじない


    @classmethod
    def to_label(cls):
        """
        ラベルデータの作成
        """
        # cls.__dict__の中からクラス変数の情報だけを抽出
        class_variables=dict(filter(lambda item: not re.fullmatch("__.*__",item[0]), cls.__dict__.items()))
        text=""
        index=0
        for name,unit in class_variables.items():
            text+=f"{index}:{name}{unit},  "
            index+=1
        text=text[:-3]
        return text


    def __iter__(self):
        """
        配列として扱えるようにするための関数
        """
        yield from  list(self.__dict__.values()) #変数をリストにして返す

    


class BaseGlobalMeta(type):
    def __setattr__(self, __name: str, __value: Any) -> None:
        """
        あとから要素を追加するのを阻止
        """
        if hasattr(self,__name):
            super().__setattr__(__name,__value)
        else:
            raise UserUtilityError(f"{__name}は{self.__name__}に最初に定義された変数に含まれていません。\n 使用する変数は宣言時に定義しておいてください")

# class BaseGlobal(metaclass=BaseGlobalMeta):
#     """
#     グローバル変数をクラス変数として管理することでglobal宣言のし忘れによるエラーをなくしたい
#     """
    
#     def __new__(cls,*p) :
#         """インスタンスの作成禁止"""
#         raise UserUtilityError(f"{cls.__name__}はインスタンス化することはできません。\n {cls.__name__}.'変数名'='値'で代入してください")


# class Parameter(BaseGlobal):
#     p1=100
#     p2="aaa"

# print(Parameter.p1)
# Parameter.p2="nnn"
# print(Parameter.p2)

# p=Parameter()

# class LocalValueNodeVisiter(ast.NodeVisitor):
#     """
#     グローバル変数と同名のローカル変数の使用を禁止するためのクラス
#     LocalValueNodeVisiter().check_localvals(f)で使用 (fは関数)
#     """

#     localvals=[]
#     globalvals=[]

#     def _check_addlocal(self,id):
#         return (id not in self.globalvals) and (id not in self.localvals)

#     def visit_Assign(self, node: ast.Assign):
#         """
#         この名前の関数を定義すると、
#         NodeVisitor.visit()の実行時に
#         Assign属性のノードを見つけたときにこの関数を呼んでくれるらしい
#         """
#         targets=node.targets
#         for target in targets:
#             if type(target) is ast.Name:
#                 if self._check_addlocal(id:=target.id):
#                     self.localvals.append(id)
#             if type(target) is ast.Tuple:
#                 elts=target.elts
#                 if self._check_addlocal(elts[0].id):
#                     self.localvals.append(elts[0].id)
#                 if self._check_addlocal(elts[1].id):
#                     self.localvals.append(elts[1].id)
            
#         self.generic_visit(node)

#     def visit_Global(self, node: ast.Global):
#         self.globalvals += node.names
#         self.generic_visit(node)

#     def visit_NamedExpr(self, node: ast.NamedExpr):
#         if type(node.target) is ast.Name:
#             if self._check_addlocal(id:=node.target.id):
#                 self.localvals.append(id)

#         self.generic_visit(node)
    
#     def check_localvals(self,f:Callable):
#         self.visit(ast.parse(inspect.getsource(f)))
#         for localval in self.localvals:
#             if localval in globals():
#                 raise UserUtilityError(f"変数'{localval}'はグローバル変数とローカル変数の両方で定義されています。\n グローバル変数として使いたいときはグローバル宣言(global 変数名)をおこなってください")