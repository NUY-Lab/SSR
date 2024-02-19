from pathlib import Path

from macro import get_macro, get_macropath
from variables import USER_VARIABLES, init


def test_get_macropath(tmp_path: Path, monkeypatch):
    init(tmp_path)
    USER_VARIABLES.DATADIR = tmp_path / "user_data"
    USER_VARIABLES.TEMPDIR = tmp_path / "user_temp"
    USER_VARIABLES.MACRODIR = tmp_path / "user_macro"

    macro_path = tmp_path / "macro.py"
    monkeypatch.setattr("macro.ask_open_filename", lambda **arg: macro_path)

    path, name, dir = get_macropath()

    assert path == macro_path
    assert name == macro_path.stem
    assert dir == macro_path.parent


def test_get_macro(tmp_path: Path):
    macro_path = tmp_path / "macro.py"
    macro_path.write_text(
        """
def start():
    pass

def update():
    return false

def end():
    pass
    
def split(path):
    pass
    
def after(path):
    pass
"""
    )

    macro = get_macro(macro_path)

    assert callable(macro.start)
    assert callable(macro.update)
    assert callable(macro.end)
    assert callable(macro.split)
    assert callable(macro.after)


def test_get_macro_minimum(tmp_path: Path):
    macro_path = tmp_path / "macro.py"
    macro_path.write_text(
        """
def update():
    return false
"""
    )

    macro = get_macro(macro_path)

    assert macro.start is None
    assert callable(macro.update)
    assert macro.end is None
    assert macro.split is None
    assert macro.after is None
