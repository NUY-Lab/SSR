import ast
import sys
import textwrap
import unittest
from importlib.util import module_from_spec, spec_from_loader

sys.path.append("../")
import os
from importlib.machinery import SourceFileLoader

from measure.macro_grammar import RedefinitionError, redefinition_check

count = 0


def check(text):
    sys.dont_write_bytecode = True
    global count
    count += 1
    filename = f"testtemp{count}.py"

    text = textwrap.dedent(text)  # 文字列を左寄せ

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    spec = spec_from_loader(filename, SourceFileLoader(filename, filename))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    try:
        redefinition_check(target)
    except RedefinitionError as e:
        os.remove(filename)
        return e.local_name, e.parent_name
    os.remove(filename)
    return None, None


def printnode(text):
    text = textwrap.dedent(text)  # 文字列を左寄せ
    node = ast.parse(text)
    print(ast.dump(node, indent=4))


def test1():
    text = """
    a=1
    def fn1():
        a=10
    """
    assert check(text)[0] == "a"

    text = """
    a: int
    def fn1():
        a=10
    """
    assert check(text)[0] == "a"

    text = """
    a=10
    b=0
    def fn1():
        global a
        b=0
    """
    assert check(text)[0] == "b"

    text = """
    a=10
    b=0
    def fn1(b):
        global a
        a=0
    """
    assert check(text)[0] == "b"

    text = """
    a=10
    def fn1(b):
        global a
        def fn2():
            a=10
    """
    assert check(text)[0] == "a"

    text = """
    a=10
    def fn1(b):
        a=10
        def fn2():
            global a
            a=10
    """
    assert check(text)[0] == "a"

    text = """
    def fn1():
        global a
        a=10

    def fn2():
        a=0
    """
    assert check(text)[0] == "a"

    text = """
    def fn1():
        a=10
        def fn2():
            a=1
    """
    assert check(text)[0] is None

    text = """
    a=1
    def fn1():
        if (a:=10)==10:
            b=1
    """
    assert check(text)[0] == "a"

    text = """
    (a,b)=(19,10)
    def fn1():
        a=1
    """
    assert check(text)[0] == "a"

    text = """
    (a,b)=(c,d)=(19,10)
    def fn1():
        d=1
    """
    assert check(text)[0] == "d"

    text = """
    def fn1(a):
        a=1
    """
    assert check(text)[0] is None

    text = """
    a=1
    a=10
    """
    assert check(text)[0] is None

    text = """
    a=1
    class cl1:
        a=1
    """
    assert check(text)[0] == "a"

    text = """
    a=1
    class cl1:
        def __init__(self):
            self.a=11
    """
    assert check(text)[0] is None

    text = """
    a=1
    class cl1:
        def __init__(self):
            a=10
    """
    assert check(text)[0] == "a"
    assert check(text)[1] == "__init__"

    text = """
    a=1
    class cl1:
        def __init__(self):
            global a
            a=10
    """
    assert check(text)[0] is None

    text = """
    a=1
    def fn1(b):
        b=10

    fn1(a:=11)
    c=9
    def fn2(d):
        d=fn1(c:=0)
    """
    assert check(text)[0] == "c"

    text = """
    a=1
    def fn133(b):
        a+=10

    """
    assert check(text)[0] == "a"
    assert check(text)[1] == "fn133"

    text = """
    a=[1]
    def fn1(b):
        a[0]+=1

    """
    assert check(text)[0] is None

    text = """
    
    def fn1t(b):
        global x
        x=10
    def hg():
        x=19

    """
    assert check(text)[0] == "x"
    assert check(text)[1] == "hg"

    text = """
    def fn1t(b):
        global x
        x=10
    def hgf():
        x=19
    x=19

    """
    assert check(text)[0] == "x"
    assert check(text)[1] == "hgf"

    text = """
    def h1g():
        x=19
    x=19

    """
    assert check(text)[0] == "x"
    assert check(text)[1] == "h1g"

    text = """
    g=0
    def fn3t(b):
        d=10
        def bgg(d):
            def bhh(g:int):
                b=10 

    """
    assert check(text)[0] == "g"
    assert check(text)[1] == "bhh"


def test1():
    text = """
    list=12
    """
    assert check(text)[0] == "list"

    text = """
    def ghy():
        str=10
    """
    assert check(text)[0] == "str"

    text = """
    def ghy():
        str1=10
    """
    assert check(text)[0] is None

    text = """
    class ftr:
        dict=11
    """
    assert check(text)[0] == "dict"
