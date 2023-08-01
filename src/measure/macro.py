"""
マクロの読み込みなど
"""
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from logging import getLogger
from pathlib import Path
from types import ModuleType
from typing import Callable

from .error import SSRError
from .variable import SHARED_VARIABLES

logger = getLogger(__name__)


class MacroError(SSRError):
    """マクロ関連のエラー"""


@dataclass
class MeasureMacro:
    start: Callable[[], None] | None
    update: Callable[[], False]
    end: Callable[[], None] | None
    on_command: Callable[[], None] | None
    split: Callable[[str], None] | None
    after: Callable[[str], None] | None


def get_prev_macro_name() -> str | None:
    cache = SHARED_VARIABLES.TEMPDIR / "premacroname"
    try:
        return Path(cache.read_text(encoding="utf-8")).name
    except FileNotFoundError:
        return None


def save_current_macro_name(name: str) -> None:
    cache = SHARED_VARIABLES.TEMPDIR / "premacroname"
    cache.write_text(name, encoding="utf-8")


def load_module(path: Path) -> ModuleType:
    name = path.stem

    # importlibを使って動的にpythonファイルを読み込む
    spec = spec_from_loader(name, SourceFileLoader(name, str(path)))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    return target


def load_macro(path: Path) -> MeasureMacro:
    """パスから各種関数を読み込んでユーザーマクロを返す"""
    target = load_module(path)

    # 測定マクロに必要な関数と引数が含まれているか確認
    UNDIFINE_ERROR = False
    UNDIFINE_WARNING = []
    if not hasattr(target, "start"):
        start = None
        UNDIFINE_WARNING.append("start")
    elif target.start.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".startには引数を設定してはいけません")
        UNDIFINE_ERROR = True
    else:
        start = target.start

    if not hasattr(target, "update"):
        logger.error(target.__name__ + ".pyの中でupdateを定義する必要があります")
        UNDIFINE_ERROR = True
    elif target.update.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".updateには引数を設定してはいけません")
        UNDIFINE_ERROR = True
    else:
        update = target.update

    if not hasattr(target, "end"):
        end = None
        UNDIFINE_WARNING.append("end")
    elif target.end.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".endには引数を設定してはいけません")
        UNDIFINE_ERROR = True
    else:
        end = target.end

    if not hasattr(target, "on_command"):
        on_command = None
        UNDIFINE_WARNING.append("on_command")
    elif target.on_command.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".on_commandには引数を設定してはいけません")
        UNDIFINE_ERROR = True
    else:
        on_command = target.on_command

    if hasattr(target, "bunkatsu"):
        target.split = target.bunkatsu
        logger.warning("bunkatsu関数は非推奨です。splitという名前に変えてください")

    if not hasattr(target, "split"):
        split = None
        UNDIFINE_WARNING.append("split")
    elif target.split.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".splitには引数filepathだけを設定しなければいけません")
        UNDIFINE_ERROR = True
    else:
        split = target.split

    if not hasattr(target, "after"):
        after = None
        UNDIFINE_WARNING.append("after")
    elif target.after.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".afterには引数filepathだけを設定しなければいけません")
        UNDIFINE_ERROR = True
    else:
        after = target.after

    if len(UNDIFINE_WARNING) > 0:
        logger.info(f"UNDEFINED FUNCTION: {','.join(UNDIFINE_WARNING)}")

    if UNDIFINE_ERROR:
        raise MacroError("macroの関数定義が正しくありません")

    return MeasureMacro(start, update, end, on_command, split, after)


def load_split_macro(path: Path) -> ModuleType:
    """マクロファイルを分割マクロに変換"""
    target = load_module(path)

    if hasattr(target, "bunkatsu"):
        target.split = target.bunkatsu
        logger.warning("bunkatsu関数は非推奨です。splitという名前に変えてください")

    if not hasattr(target, "split"):
        raise MacroError(f"{target.__name__}.pyにはsplit関数を定義する必要があります")
    elif target.split.__code__.co_argcount != 1:
        raise MacroError(f"{target.__name__}.splitには1つの引数が必要です")

    return target


def load_recalculate_macro(path: Path) -> Path:
    """マクロファイルを再計算マクロに変換"""
    target = load_module(path)

    if not hasattr(target, "recalculate"):
        raise MacroError(f"{target.__name__}.pyにはrecalculate関数を定義する必要があります")
    elif target.recalculate.__code__.co_argcount != 1:
        raise MacroError(f"{target.__name__}.recalculateには1つの引数が必要です")

    return target
