# ユーザー用の設定

from logging import getLogger
from pathlib import Path

from .error import SSRError
from .variable import SHARED_VARIABLES, USER_VARIABLES

logger = getLogger(__name__)


class SettingFileError(SSRError):
    """設定ファイル関係のエラー"""


def get_prev_setting_path() -> Path | None:
    cache = SHARED_VARIABLES.TEMPDIR / "deffilepath"
    try:
        return Path(cache.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def save_current_setting_path(path: Path) -> None:
    cache = SHARED_VARIABLES.TEMPDIR / "deffilepath"
    cache.write_text(str(path), encoding="utf-8")


def load_settings(path: Path) -> None:
    datadir = None
    tmpdir = None
    macrodir = None

    with path.open(encoding="utf-8") as f:
        for l in f:
            [key, value] = l.split("=")
            match key.strip():
                case "DATADIR":
                    datadir = Path(value.strip())
                case "TMPDIR":
                    tmpdir = Path(value.strip())
                case "MACRODIR":
                    macrodir = Path(value.strip())

    # 最後まで見てDATADIRが無ければエラー表示
    if datadir is None:
        raise SettingFileError("定義ファイルにDATADIRの定義がありません")
    # 相対パスなら定義ファイルからの絶対パスに変換
    if not datadir.is_absolute():
        datadir = path.parent / datadir
    # データフォルダが存在しなければエラー
    if not datadir.is_dir():
        raise SettingFileError(f"{datadir}は定義ファイルに設定されていますが存在しません")

    if tmpdir is None:
        raise SettingFileError("定義ファイルにTMPDIRの定義がありません")
    if not tmpdir.is_absolute():
        tmpdir = path.parent / tmpdir
    if not tmpdir.is_dir():
        raise SettingFileError(f"{tmpdir}は定義ファイルに設定されていますが存在しません")

    if macrodir is None:
        logger.warning("you can set MACRODIR in your define file")
    else:
        if not macrodir.is_absolute():
            macrodir = path.parent / macrodir
        if not macrodir.is_dir():
            logger.warning("%sは定義ファイルに設定されていますが存在しません", macrodir)
            macrodir = None

    USER_VARIABLES.DATADIR = datadir
    USER_VARIABLES.TEMPDIR = tmpdir
    USER_VARIABLES.MACRODIR = macrodir
