import io
from pathlib import Path

from cli.meas import meas

SETTING = (Path.cwd() / "example/demo/example.def").absolute()
MACRO = (Path.cwd() / "example/demo/macro/demo/template.py").absolute()


def ask_open_filename(**args):
    if "設定ファイル" in args["title"]:
        return SETTING
    elif "マクロ" in args["title"]:
        return MACRO


def test_meas(monkeypatch):
    monkeypatch.setattr("cli.meas.ask_open_filename", ask_open_filename)

    meas()
