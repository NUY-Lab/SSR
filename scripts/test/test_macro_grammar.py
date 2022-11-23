import ast
import sys
import textwrap
import unittest

sys.path.append("../")

from macro_grammar import RedefinitionCheckNodeVisitor, _redefinition_check


def check(text):
    text=textwrap.dedent(text) # 文字列を左寄せ
    node=ast.parse(text)
    try:
        _redefinition_check(node)
    except RedefinitionCheckNodeVisitor.RedefinitionError as e:
        return e.varname
    return ""

def printnode(text):
    text=textwrap.dedent(text) # 文字列を左寄せ
    node=ast.parse(text)
    print(ast.dump(node,indent=4))

class TestLocalCheck(unittest.TestCase):

    def test1(self):
        
        text="""
        a=1
        def fn1():
            a=10
        """
        self.assertEqual("a",check(text))


        
        text="""
        a: int
        def fn1():
            a=10
        """
        self.assertEqual("a",check(text))


        
        text="""
        a=10
        def fn1():
            a:int
        """
        self.assertEqual("a",check(text))


        
        text="""
        a=10
        b=0
        def fn1():
            global a
            b=0
        """
        self.assertEqual("b",check(text))

        text="""
        a=10
        b=0
        def fn1(b):
            global a
            a=0
        """
        self.assertEqual("b",check(text))

        text="""
        a=10
        def fn1(b):
            global a
            def fn2():
                a=10
        """
        self.assertEqual("a",check(text))

        text="""
        a=10
        def fn1(b):
            a=10
            def fn2():
                global a
                a=10
        """
        self.assertEqual("a",check(text))

        text="""
        def fn1():
            global a
            a=10

        def fn2():
            a=0
        """
        self.assertEqual("a",check(text))

        text="""
        def fn1():
            a=10
            def fn2():
                a=1
        """
        self.assertEqual("a",check(text))

        text="""
        def fn1():
            a=10
            def fn2():
                nonlocal a
                a=1
        """
        self.assertEqual("",check(text))

        text="""
        def fn1():
            a=10
            def fn2(a):
                b=1
        """
        self.assertEqual("a",check(text))

        text="""
        a=1
        def fn1():
            if (a:=10)==10:
                b=1
        """
        self.assertEqual("a",check(text))


        text="""
        (a,b)=(19,10)
        def fn1():
            a=1
        """
        self.assertEqual("a",check(text))

        text="""
        (a,b)=(c,d)=(19,10)
        def fn1():
            d=1
        """
        self.assertEqual("d",check(text))

        text="""
        def fn1(a):
            a=1
        """
        self.assertEqual("",check(text))

        text="""
        a=1
        a=10
        """
        self.assertEqual("",check(text))

        text="""
        a=1
        class cl1:
            a=1
        """
        self.assertEqual("a",check(text))

        text="""
        a=1
        class cl1:
            self.a=1
        """
        self.assertEqual("",check(text))

        text="""
        a=1
        class cl1:
            def __init__(self):
                a=10
        """
        self.assertEqual("a",check(text))

        text="""
        a=1
        class cl1:
            def __init__(self):
                global a
                a=10
        """
        self.assertEqual("",check(text))

        text="""
        a=1
        def fn1(b):
            b=10

        fn1(a:=11)
        c=9
        def fn2(d):
            d=fn1(c:=0)
        """
        self.assertEqual("c",check(text))

        text="""
        a=1
        def fn1(b):
            a+=10

        """
        self.assertEqual("a",check(text))

        text="""
        a=[1]
        def fn1(b):
            a[0]+=1

        """
        
        self.assertEqual("",check(text))

   