import ast
import sys
import textwrap
import unittest
from importlib import reload
from importlib.util import module_from_spec, spec_from_loader
from types import ModuleType

sys.path.append("../")
import inspect
import os
import time
from importlib.machinery import SourceFileLoader

from macro_grammar import RedefinitionError, redefinition_check
from utility import MyException

count=0
def check(text):
    sys.dont_write_bytecode = True
    global count
    count+=1
    filename=f"testtemp{count}.py"
    
    text=textwrap.dedent(text) # 文字列を左寄せ

    with open(filename,"w",encoding="utf-8") as f:
        f.write(text)


    
    spec = spec_from_loader(filename, SourceFileLoader(filename, filename))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    
    
    try:
        redefinition_check(target)
    except RedefinitionError as e:
        os.remove(filename)
        return e.local_name,e.parent_name
    os.remove(filename)
    return None,None

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
        self.assertEqual("a",check(text)[0])


        
        text="""
        a: int
        def fn1():
            a=10
        """
        self.assertEqual("a",check(text)[0])


        


        
        text="""
        a=10
        b=0
        def fn1():
            global a
            b=0
        """
        self.assertEqual("b",check(text)[0])

        text="""
        a=10
        b=0
        def fn1(b):
            global a
            a=0
        """
        self.assertEqual("b",check(text)[0])

        text="""
        a=10
        def fn1(b):
            global a
            def fn2():
                a=10
        """
        self.assertEqual("a",check(text)[0])

        text="""
        a=10
        def fn1(b):
            a=10
            def fn2():
                global a
                a=10
        """
        self.assertEqual("a",check(text)[0])

        text="""
        def fn1():
            global a
            a=10

        def fn2():
            a=0
        """
        self.assertEqual("a",check(text)[0])

        text="""
        def fn1():
            a=10
            def fn2():
                a=1
        """
        self.assertEqual(None,check(text)[0])

        

        text="""
        a=1
        def fn1():
            if (a:=10)==10:
                b=1
        """
        self.assertEqual("a",check(text)[0])


        text="""
        (a,b)=(19,10)
        def fn1():
            a=1
        """
        self.assertEqual("a",check(text)[0])

        text="""
        (a,b)=(c,d)=(19,10)
        def fn1():
            d=1
        """
        self.assertEqual("d",check(text)[0])

        text="""
        def fn1(a):
            a=1
        """
        self.assertEqual(None,check(text)[0])

        text="""
        a=1
        a=10
        """
        self.assertEqual(None,check(text)[0])

        text="""
        a=1
        class cl1:
            a=1
        """
        self.assertEqual("a",check(text)[0])

        text="""
        a=1
        class cl1:
            def __init__(self):
                self.a=11
        """
        self.assertEqual(None,check(text)[0])

        text="""
        a=1
        class cl1:
            def __init__(self):
                a=10
        """
        self.assertEqual("a",check(text)[0])
        self.assertEqual("__init__",check(text)[1])

        text="""
        a=1
        class cl1:
            def __init__(self):
                global a
                a=10
        """
        self.assertEqual(None,check(text)[0])

        text="""
        a=1
        def fn1(b):
            b=10

        fn1(a:=11)
        c=9
        def fn2(d):
            d=fn1(c:=0)
        """
        self.assertEqual("c",check(text)[0])

        text="""
        a=1
        def fn133(b):
            a+=10

        """
        self.assertEqual("a",check(text)[0])
        self.assertEqual("fn133",check(text)[1])

        text="""
        a=[1]
        def fn1(b):
            a[0]+=1

        """
        
        self.assertEqual(None,check(text)[0])

        text="""
        
        def fn1t(b):
            global x
            x=10
        def hg():
            x=19

        """
        
        self.assertEqual("x",check(text)[0])
        self.assertEqual("hg",check(text)[1])

        text="""
        def fn1t(b):
            global x
            x=10
        def hgf():
            x=19
        x=19

        """
        
        self.assertEqual("x",check(text)[0])
        self.assertEqual("hgf",check(text)[1])
        
        text="""
        def h1g():
            x=19
        x=19

        """
        
        self.assertEqual("x",check(text)[0])
        self.assertEqual("h1g",check(text)[1])


        text="""
        g=0
        def fn3t(b):
            d=10
            def bgg(d):
                def bhh(g:int):
                    b=10 

        """
        
        self.assertEqual("g",check(text)[0])
        self.assertEqual("bhh",check(text)[1])

    
    def test1(self):
        
        text="""
        list=12
        """
        self.assertEqual("list",check(text)[0])

        text="""
        def ghy():
            str=10
        """
        self.assertEqual("str",check(text)[0])

        text="""
        def ghy():
            str1=10
        """
        self.assertEqual(None,check(text)[0])

        text="""
        class ftr:
            dict=11
        """
        self.assertEqual("dict",check(text)[0])