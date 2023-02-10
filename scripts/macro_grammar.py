"""
ユーザーマクロの文法に制限を追加するクラス
書き間違え、意図しない挙動を減らすことが目的

SSRでは、global宣言忘れによるエラーを危惧して、グローバル変数と同名のローカル変数を定義できないようにしている
"""
import ast
import inspect
import re
from types import CodeType, FunctionType, ModuleType
from typing import List

from utility import MyException


def macro_grammer_check(module: ModuleType):
    redefinition_check(module)


class RedefinitionError(MyException):
    """多重定義エラー

    python自体はglobalとlocalで同名の変数定義が許容されるが、バグのもとになりそうなのでSSRでは一律に禁止する
    """


def redefinition_check(mod: ModuleType):
    """マクロの中にグローバル変数とローカル変数が同じ名前で定義されていたらエラーを返す関数"""
    dic = dict(
        filter(lambda item: not re.match("__.*__", item[0]), mod.__dict__.items())
    )  # グローバル空間の変数名のうち、自分で定義したものを抽出
    dic = dict(
        filter(lambda item: inspect.getmodule(item[1]) is None, dic.items())
    )  # importした関数などは排除
    if (annot := mod.__dict__.get("__annotations__")) is None:
        annot = []
    else:
        annot = list(annot.keys())  # グローバル空間のアノテーションもグローバル変数に追加

    global_vars = list(dic.keys()) + get_global_keywards(mod) + annot

    builtins = __builtins__.keys()  # ビルトイン変数

    def global_check(
        locals: List[str],
        parent_name: str,
        parent_type_japanese: str,
        variable_type_japanese: str,
    ):
        """グローバル変数と同名のローカル変数がないかチェック"""
        nonlocal global_vars, builtins
        for l in locals:
            if l in global_vars:
                error = RedefinitionError(
                    f"{parent_type_japanese}{parent_name}内の{variable_type_japanese}{l}はグローバル変数として定義されています。\nグローバル変数として使いたい場合はglobal宣言を行ってください。\nローカル変数として使いたい場合は別の名前を用いてください"
                )
                error.local_name = l
                error.parent_name = parent_name
                raise error

    def builtin_check(
        locals: List[str],
        parent_name: str,
        parent_type_japanese: str,
        variable_type_japanese: str,
    ):
        """ビルトイン関数と同名のローカル変数がないかチェック"""
        nonlocal builtins
        for l in locals:
            if l in builtins:
                error = RedefinitionError(
                    f"{parent_type_japanese}{parent_name}内の{variable_type_japanese}{l}はPythonに標準で定義されている変数です。別の名前に変えてください"
                )
                error.local_name = l
                error.parent_name = parent_name
                raise error

    def code_check(code: CodeType):
        """関数の中のローカル変数をチェック"""
        locals = code.co_varnames + code.co_consts + code.co_cellvars
        global_check(locals, code.co_name, "関数", "ローカル変数")
        builtin_check(locals, code.co_name, "関数", "ローカル変数")
        for c in code.co_consts:
            if type(c) is CodeType:
                code_check(c)
            if type(c) is type:
                class_check(c)

    def class_check(cls: type):
        """クラス変数とグローバル変数が被っていないかチェック"""
        members = cls.__dict__  # クラス.__dict__の中に変数情報が入っているので取り出す
        annot = (
            list(cls.__annotations__.keys()) if hasattr(cls, "__annotations__") else []
        )
        locals = list(
            filter(lambda x: not re.match("__.*__", x), list(members.keys()) + annot)
        )
        global_check(locals, cls.__name__, "クラス", "メンバ変数")
        builtin_check(locals, cls.__name__, "クラス", "メンバ変数")
        for m in members.values():
            if type(m) is FunctionType:  # クラス内のメソッドをチェック
                code_check(m.__code__)
            if type(m) is type:  # クラス内クラスをチェック
                class_check(m)

    builtin_check(global_vars, "マクロ", "", "グローバル変数")

    for v in dic.values():
        if type(v) is FunctionType:
            code_check(v.__code__)
        if type(v) is type:
            class_check(v)


def get_global_keywards(mod: ModuleType):
    class GlobalVisitor(ast.NodeVisitor):
        """グローバル宣言された変数を取ってくるクラス"""

        global_vars = []

        def visit_Global(self, node: ast.Global):
            for n in node.names:
                self.global_vars.append(n)

        def get_global_vars(self, node: ast.AST):
            self.visit(node)
            return self.global_vars

    return GlobalVisitor().get_global_vars(ast.parse(inspect.getsource(mod)))
