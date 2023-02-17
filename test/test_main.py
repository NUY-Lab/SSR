import io
from pathlib import Path

from scripts.MAIN import main


def test_main(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("MEAS\n"))
    monkeypatch.setattr(
        "define.ask_open_filename",
        lambda **args: Path("./sample/example.def").absolute(),
    )
    monkeypatch.setattr(
        "macro.ask_open_filename",
        lambda **args: Path("./sample/macro/テンプレートマクロ/template.py").absolute(),
    )
    main()
