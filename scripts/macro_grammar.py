"""
    ユーザーマクロの文法に制限を追加するクラス
    書き間違え、意図しない挙動を減らすことが目的
"""
import ast
import inspect
import textwrap
from types import ModuleType
from typing import Callable, Union

from utility import MyException


def macro_grammer_check(module:ModuleType):
    node=ast.parse(inspect.getsource(module))
    _redefinition_check(node)




class GlobalVariablesNodeVisitor(ast.NodeVisitor):
    """global宣言された変数を全て取ってくる"""
    def __init__(self) -> None:
        self.global_list=[]
        super().__init__()

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            self.global_list.append(name)

    
    


class RedefinitionCheckNodeVisitor(ast.NodeVisitor):

    class RedefinitionError(MyException):
        """変数の再定義エラー"""
        def __init__(self, linenum,varname):
            super().__init__(f"{linenum}行目の変数''{varname}''は上の階層で一度定義された変数です。\n上の階層で定義した変数と同じものとして使うならglobalもしくはnonlocal宣言を行ってください。\n上の階層とは別の変数として使うなら別の変数名を使ってください。")
            self.linenum=linenum
            self.varname=varname
    def __init__(self) -> None:
        self.nowlevel_vars_list=[] #ローカル変数のリスト
        self.highlevel_vars_list=[] #上位階層のリスト
        self.declare_vars_list=[] #global宣言された変数
        self.children_nodes=[]
        super().__init__()

    def append_var(self,name,linenum):
        """global,nonlocal宣言された変数でなければリストに追加"""

        if name not in self.declare_vars_list:
            if name in self.highlevel_vars_list:
                raise self.RedefinitionError(linenum,name)
            else:
                self.nowlevel_vars_list.append(name)
        
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """代入(=)"""
        for target in node.targets: # x=y=19などの書き方だと node.targetsの要素が2つ以上になる
            # Name,Tuple以外にもAttribute(Class.attr=value)やSubscript(list[num]=value)があるが
            # それらはローカル変数を作成しないので排除
            if type(target) is ast.Name:
                self.append_var(target.id,node.lineno)
            elif type(target) is ast.Tuple:
                for element in target.elts:
                    self.append_var(element.id,node.lineno)

        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """代入式(:=)"""
        if type(tar:=node.target) is ast.Name:# python3.9.12では代入式にTuple,Attribute,Subscriptは使えないっぽいが一応書いておく
            self.append_var(tar.id,node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """var:floatみたいなやつ"""
        if type(node.target) is ast.Name:
            self.append_var(node.target.id,node.lineno)
        self.generic_visit(node)
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """代入演算子(+=)"""
        if type(node.target) is ast.Name:
            self.append_var(node.target.id,node.lineno)
        self.generic_visit(node)

    def check_argument(self, node:Union[ast.FunctionDef,ast.AsyncFunctionDef] ) ->None:
        """関数の引数もローカル変数に含める"""
        linenum=node.lineno
        def check(name):
            if name in self.nowlevel_vars_list+self.highlevel_vars_list:
                raise self.RedefinitionError(linenum,name)
        node=node.args
        for arg in node.args: #普通の引数
            check(arg.arg)
        for arg in node.posonlyargs: #位置専用パラメータ
            check(arg.arg)
        for arg in node.kwonlyargs: #キーワード専用パラメータ
            check(arg.arg)
        if node.vararg is not None: # キーワード引数のtuple化
            check(node.vararg.arg)
        if node.kwarg is not None: # キーワード引数の辞書化
            check(node.kwarg.arg)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        """global宣言された変数を取得"""
        for name in node.names:
            self.declare_vars_list.append(name)
        self.generic_visit(node)
    
    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        """nonlocal宣言された変数を取得"""
        for name in node.names:
            self.declare_vars_list.append(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.append_var(node.name,node.lineno) #関数名やクラス名もローカル変数としてリストに入れる
        self.check_argument(node)
        self.children_nodes.append(node)
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.append_var(node.name,node.lineno)
        self.children_nodes.append(node)
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.append_var(node.name,node.lineno)
        self.check_argument(node)
        self.children_nodes.append(node)


    def check_local(self,tree:ast.AST):
        
        super().generic_visit(tree)
        """さらに下の階層があれば新しいインスタンスを作成してチェックさせる"""
        for childlennode in self.children_nodes:
            
            visitor=RedefinitionCheckNodeVisitor()
            visitor.highlevel_vars_list=self.highlevel_vars_list+self.nowlevel_vars_list
            visitor.check_local(childlennode)



    


def _redefinition_check(node:ast.AST):
    """
    ユーザーマクロ内で上位レイヤーで定義された変数と同名の変数を再定義していたらエラーを吐く
    同じスコープ内での再代入は検知しない
    """
    
    visitor=GlobalVariablesNodeVisitor()
    visitor.visit(node)
    global_list=visitor.global_list
    
        

    localvisitor=RedefinitionCheckNodeVisitor()
    localvisitor.declare_vars_list=global_list
    localvisitor.highlevel_vars_list=global_list
    localvisitor.check_local(node)

