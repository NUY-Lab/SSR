from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from utility import get_date_text, get_encode_type


def test_get_encode_type(tmp_path: Path):
    ascii_file_path = tmp_path / "ascii.txt"
    utf8_file_path = tmp_path / "utf8.txt"
    sjis_file_path = tmp_path / "sjis.txt"

    ascii_file_path.write_text("ascii file", encoding="ascii")
    utf8_file_path.write_text("utf-8ファイル", encoding="utf-8")
    sjis_file_path.write_text("sjisファイル", encoding="sjis")

    assert get_encode_type(str(ascii_file_path)) == "utf-8"
    assert get_encode_type(str(utf8_file_path)) == "utf-8"
    assert get_encode_type(str(sjis_file_path)) == "SHIFT_JIS"


def test_get_date_text(monkeypatch):
    # now() だけをモックした datetime_mock を作成
    datetime_mock = MagicMock(wraps=datetime)
    datetime_mock.now.return_value = datetime(2021, 4, 1, 12, 0, 0)

    # datetime.datetime を datetime_mock で置き換え
    monkeypatch.setattr("datetime.datetime", datetime_mock)

    assert get_date_text() == "210401-120000"
