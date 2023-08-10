from pathlib import Path

import pytest

from measure.setting import (
    SettingFileError,
    get_prev_setting_path,
    load_settings,
    save_current_setting_path,
)


def test_setting_path(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("measure.setting.TMPDIR", tmp_path)

    assert get_prev_setting_path() is None

    setting_path = tmp_path / "setting.def"
    save_current_setting_path(setting_path)

    assert get_prev_setting_path() == setting_path


def test_load_setting(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    tmpdir_path = tmp_path / "tmp"
    macrodir_path = tmp_path / "macro"

    datadir_path.mkdir()
    tmpdir_path.mkdir()
    macrodir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR  = {str(datadir_path)}
TMPDIR   = {str(tmpdir_path)}
MACRODIR = {str(macrodir_path)}
"""
        )

    datadir, tmpdir, macrodir = load_settings(setting_path)

    assert datadir == datadir_path
    assert tmpdir == tmpdir_path
    assert macrodir == macrodir_path


def test_load_setting_no_datadir_field(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    tmpdir_path = tmp_path / "tmp"
    macrodir_path = tmp_path / "macro"

    tmpdir_path.mkdir()
    macrodir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
TMPDIR   = {str(tmpdir_path)}
MACRODIR = {str(macrodir_path)}
"""
        )

    with pytest.raises(SettingFileError):
        datadir, tmpdir, macrodir = load_settings(setting_path)


def test_load_setting_no_datadir_direcotry(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    tmpdir_path = tmp_path / "tmp"
    macrodir_path = tmp_path / "macro"

    tmpdir_path.mkdir()
    macrodir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR  = {str(datadir_path)}
TMPDIR   = {str(tmpdir_path)}
MACRODIR = {str(macrodir_path)}
"""
        )

    with pytest.raises(SettingFileError):
        datadir, tmpdir, macrodir = load_settings(setting_path)


def test_load_setting_no_tmpdir_field(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    macrodir_path = tmp_path / "macro"

    datadir_path.mkdir()
    macrodir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR   = {str(datadir_path)}
MACRODIR = {str(macrodir_path)}
"""
        )

    with pytest.raises(SettingFileError):
        datadir, tmpdir, macrodir = load_settings(setting_path)


def test_load_setting_no_tmpdir_direcotry(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    tmpdir_path = tmp_path / "tmp"
    macrodir_path = tmp_path / "macro"

    datadir_path.mkdir()
    macrodir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR  = {str(datadir_path)}
TMPDIR   = {str(tmpdir_path)}
MACRODIR = {str(macrodir_path)}
"""
        )

    with pytest.raises(SettingFileError):
        datadir, tmpdir, macrodir = load_settings(setting_path)


def test_load_setting_no_macrodir_field(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    tmpdir_path = tmp_path / "tmp"

    datadir_path.mkdir()
    tmpdir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR  = {str(datadir_path)}
TMPDIR   = {str(tmpdir_path)}
"""
        )

    datadir, tmpdir, macrodir = load_settings(setting_path)

    assert datadir == datadir_path
    assert tmpdir == tmpdir_path
    assert macrodir is None


def test_load_setting_no_datadir_direcotry(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    tmpdir_path = tmp_path / "tmp"
    macrodir_path = tmp_path / "macro"

    datadir_path.mkdir()
    tmpdir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR  = {str(datadir_path)}
TMPDIR   = {str(tmpdir_path)}
MACRODIR = {str(macrodir_path)}
"""
        )

    datadir, tmpdir, macrodir = load_settings(setting_path)

    assert datadir == datadir_path
    assert tmpdir == tmpdir_path
    assert macrodir is None


def test_load_setting_relative_path(tmp_path: Path):
    setting_path = tmp_path / "setting.def"
    datadir_path = tmp_path / "data"
    tmpdir_path = tmp_path / "tmp"
    macrodir_path = tmp_path / "macro"

    datadir_path.mkdir()
    tmpdir_path.mkdir()
    macrodir_path.mkdir()

    with setting_path.open(mode="w", encoding="utf-8") as f:
        f.write(
            f"""
DATADIR  = data
TMPDIR   = tmp
MACRODIR = macro
"""
        )

    datadir, tmpdir, macrodir = load_settings(setting_path)

    assert datadir == datadir_path
    assert tmpdir == tmpdir_path
    assert macrodir == macrodir_path
