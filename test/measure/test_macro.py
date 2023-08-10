from pathlib import Path

from measure.macro import get_prev_macro_name, load_macro, save_current_macro_name


def test_macro_name(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("measure.macro.TMPDIR", tmp_path)

    assert get_prev_macro_name() is None

    save_current_macro_name("macro name")

    assert get_prev_macro_name() == "macro name"


def test_load_macro(tmp_path: Path):
    macro_path = tmp_path / "macro.py"

    with macro_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            """
def update():
    pass
"""
        )

    macro = load_macro(macro_path)

    assert macro.start is None
    assert callable(macro.update)
    assert macro.end is None
    assert macro.on_command is None
    assert macro.split is None
    assert macro.after is None


def test_load_macro_all_function(tmp_path: Path):
    macro_path = tmp_path / "macro.py"

    with macro_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            """
def start():
    pass

def update():
    pass

def end():
    pass

def on_command(command):
    pass

def split(path):
    pass

def after(path):
    pass
"""
        )

    macro = load_macro(macro_path)

    assert callable(macro.start)
    assert callable(macro.update)
    assert callable(macro.end)
    assert callable(macro.on_command)
    assert callable(macro.split)
    assert callable(macro.after)
