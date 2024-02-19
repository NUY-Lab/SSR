from pathlib import Path

from define import get_deffile, read_deffile
from variables import USER_VARIABLES, init


def test_get_deffile(tmp_path: Path, monkeypatch):
    init(tmp_path)
    def_path = tmp_path / "define.def"
    monkeypatch.setattr("define.ask_open_filename", lambda **args: def_path)

    path = get_deffile()

    assert path == def_path


def test_read_deffile(tmp_path: Path, monkeypatch):
    init(tmp_path)
    def_path = tmp_path / "define.def"
    def_path.write_text(
        """
DATADIR=./datadir
TMPDIR=./tmpdir
MACRODIR=./macrodir
"""
    )
    (tmp_path / "datadir").mkdir()
    (tmp_path / "tmpdir").mkdir()
    (tmp_path / "macrodir").mkdir()
    monkeypatch.setattr("define.ask_open_filename", lambda **args: def_path)

    read_deffile()

    assert USER_VARIABLES.DATADIR == tmp_path / "datadir"
    assert USER_VARIABLES.TEMPDIR == tmp_path / "tmpdir"
    assert USER_VARIABLES.MACRODIR == tmp_path / "macrodir"
