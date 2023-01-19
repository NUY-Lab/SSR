"""
マクロの読み込みなど
"""
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from logging import getLogger
from pathlib import Path
from types import ModuleType

from utility import MyException, ask_open_filename
from variables import SHARED_VARIABLES, USER_VARIABLES

logger = getLogger(__name__)


class MacroError(MyException):
    """マクロ関連のエラー"""


def get_macropath() -> tuple[Path,str,Path]:
    """前回のマクロ名が保存されたファイルのパス"""
    path_premacroname = SHARED_VARIABLES.TEMPDIR / "premacroname"
    path_premacroname.touch()

    premacroname = path_premacroname.read_text(encoding="utf-8")

    # .ssrは勝手に作った拡張子
    macropath = ask_open_filename(
        filetypes=[("pythonファイル", "*.py *.ssr")],
        title="マクロを選択してください",
        initialdir=str(USER_VARIABLES.MACRODIR),
        initialfile=premacroname,
    )

    macrodir = macropath.parent
    macroname = macropath.stem

    path_premacroname.write_text(macropath.name, encoding="utf-8")
    logger.info("macro: %s", macropath.name)

    return macropath, macroname, macrodir


def get_macro(macropath: Path) -> ModuleType:
    """パスから各種関数を読み込んでユーザーマクロを返す"""
    macroname = macropath.stem

    # importlibを使って動的にpythonファイルを読み込む
    spec = spec_from_loader(macroname, SourceFileLoader(macroname, str(macropath)))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    # 測定マクロに必要な関数と引数が含まれているか確認
    UNDIFINE_ERROR = False
    UNDIFINE_WARNING = []
    if not hasattr(target, "start"):
        target.start = None
        UNDIFINE_WARNING.append("start")
    elif target.start.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".startには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "update"):
        logger.error(target.__name__ + ".pyの中でupdateを定義する必要があります")
        UNDIFINE_ERROR = True
    elif target.update.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".updateには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "end"):
        target.end = None
        UNDIFINE_WARNING.append("end")
    elif target.end.__code__.co_argcount != 0:
        logger.error(target.__name__ + ".endには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "on_command"):
        target.on_command = None
        UNDIFINE_WARNING.append("on_command")
    elif target.on_command.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".on_commandには引数を設定してはいけません")
        UNDIFINE_ERROR = True

    if hasattr(target, "bunkatsu"):
        target.split = target.bunkatsu
        logger.warning("bunkatsu 関数は非推奨です。splitという名前に変えてください")

    if not hasattr(target, "split"):
        target.split = None
        UNDIFINE_WARNING.append("split")
    elif target.split.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".splitには引数filepathだけを設定しなければいけません")
        UNDIFINE_ERROR = True

    if not hasattr(target, "after"):
        target.after = None
        UNDIFINE_WARNING.append("after")
    elif target.after.__code__.co_argcount != 1:
        logger.error(target.__name__ + ".afterには引数filepathだけを設定しなければいけません")
        UNDIFINE_ERROR = True

    if len(UNDIFINE_WARNING) > 0:
        logger.info("UNDEFINED FUNCTION: %s", ", ".join(UNDIFINE_WARNING))

    if UNDIFINE_ERROR:
        raise MacroError("macroの関数定義が正しくありません")

    return target


def get_macro_split(macroPath: Path) -> ModuleType:
    """マクロファイルを分割マクロに変換"""
    macroname = macroPath.stem
    spec = spec_from_loader(macroname, SourceFileLoader(macroname, str(macroPath)))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    if hasattr(target, "bunkatsu"):
        target.split = target.bunkatsu
        logger.warning("bunkatsu 関数は非推奨です。splitという名前に変えてください")

    if not hasattr(target, "split"):
        raise MacroError(f"{target.__name__}.pyにはsplit関数を定義する必要があります")
    elif target.split.__code__.co_argcount != 1:
        raise MacroError(f"{target.__name__}.splitには1つの引数が必要です")

    return target


def get_macro_recalculate(macroPath: Path):
    """マクロファイルを再計算マクロに変換"""
    macroname = macroPath.stem
    spec = spec_from_loader(macroname, SourceFileLoader(macroname, str(macroPath)))
    target = module_from_spec(spec)
    spec.loader.exec_module(target)

    if not hasattr(target, "recalculate"):
        raise MacroError(f"{target.__name__}.pyにはrecalculate関数を定義する必要があります")
    elif target.recalculate.__code__.co_argcount != 1:
        raise MacroError(f"{target.__name__}.recalculateには1つの引数が必要です")

    return target
