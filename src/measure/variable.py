"""共有度の高い変数を置いておく"""
from pathlib import Path

from .error import SSRError


class VariablesError(SSRError):
    """変数関係のエラー"""


class PathObject:
    """Pathインスタンスの型チェックとNoneチェックを担当

    Property
    ------------

    value: Path
        格納するPathインスタンス
    """

    __value = None

    @property
    def value(self) -> Path:
        if self.__value is None:
            raise ValueError("値がまだ入っていません。")
        return self.__value

    @value.setter
    def value(self, value: Path):
        if not isinstance(value, Path):
            raise ValueError("Pathクラスのインスタンスを代入してください")
        self.__value = value


class USER_VARIABLES:
    """各ユーザーがそれぞれ個別に持つ変数

    各プロパティに対応するセッターが存在する

    Property
    --------

    TEMPDIR: Path
        一時フォルダのパス
    DATADIR: Path
        データ保存フォルダ
    MACRODIR: Path
        測定マクロのフォルダ
    """

    __TEMPDIR = PathObject()

    @classmethod
    @property
    def TEMPDIR(cls) -> Path:
        """プロパティ"""
        return cls.__TEMPDIR.value

    @classmethod
    def set_TEMPDIR(cls, value: Path):
        """セッター"""
        cls.__TEMPDIR.value = value

    __DATADIR = PathObject()

    @classmethod
    @property
    def DATADIR(cls) -> Path:
        return cls.__DATADIR.value

    @classmethod
    def set_DATADIR(cls, value: Path):
        cls.__DATADIR.value = value

    __MACRODIR = PathObject()

    @classmethod
    @property
    def MACRODIR(cls) -> Path:
        return cls.__MACRODIR.value

    @classmethod
    def set_MACRODIR(cls, value: Path):
        cls.__MACRODIR.value = value


class SHARED_VARIABLES:
    """ユーザー間で共通してもつ変数

    各プロパティに対応するセッターが存在する
    (注)扱うときは慎重に

    Proprety
    --------

    SETTINGDIR: Path
        共有設定が保存されるフォルダのパス
    TEMPDIR: Path
        一時フォルダのパス
    SSR_SCRIPTSDIR: Path
        SSRのコードがあるフォルダのパス。
        ユーザー側から触ることはまずない
    SSR_HOMEDIR: Path
        SSR本体の存在するフォルダ
        ユーザー側から触ることはまずない
    LOGDIR: Path
        共有ログのあるフォルダ
    """

    __SETTINGDIR = PathObject()

    @classmethod
    @property
    def SETTINGDIR(cls) -> Path:
        """プロパティ"""
        return cls.__SETTINGDIR.value

    @classmethod
    def set_SETTINGDIR(cls, value: Path):
        """セッター"""
        cls.__SETTINGDIR.value = value

    __TEMPDIR = PathObject()

    @classmethod
    @property
    def TEMPDIR(cls) -> Path:
        return cls.__TEMPDIR.value

    @classmethod
    def set_TEMPDIR(cls, value: Path):
        cls.__TEMPDIR.value = value

    __SSR_SCRIPTSDIR = PathObject()

    @classmethod
    @property
    def SSR_SCRIPTSDIR(cls) -> Path:
        return cls.__SSR_SCRIPTSDIR.value

    @classmethod
    def set_SSR_SCRIPTSDIR(cls, value: Path):
        cls.__SSR_SCRIPTSDIR.value = value

    __LOGDIR = PathObject()

    @classmethod
    @property
    def LOGDIR(cls) -> Path:
        return cls.__LOGDIR.value

    @classmethod
    def set_LOGDIR(cls, value: Path):
        cls.__LOGDIR.value = value

    __SSR_HOMEDIR = PathObject()

    @classmethod
    @property
    def SSR_HOMEDIR(cls) -> Path:
        return cls.__SSR_HOMEDIR.value

    @classmethod
    def set_SSR_HOMEDIR(cls, value: Path):
        cls.__SSR_HOMEDIR.value = value


def init(home: Path):
    """変数の初期化"""

    # SSRフォルダーのパス
    SHARED_VARIABLES.set_SSR_HOMEDIR(home)

    # 共有TEMPフォルダーのパス
    tempdir = home / "temp"
    if not tempdir.is_dir():
        tempdir.mkdir()
    SHARED_VARIABLES.set_TEMPDIR(tempdir)

    # 共有設定フォルダのパス
    settingdir = home / "shared_settings"
    if not settingdir.is_dir():
        settingdir.mkdir()
    SHARED_VARIABLES.set_SETTINGDIR(settingdir)

    # scriptsフォルダーのパス
    SHARED_VARIABLES.set_SSR_SCRIPTSDIR(home / "scripts")

    # logフォルダーのパス
    logdir = home / "log"
    if not logdir.is_dir():
        logdir.mkdir()
    SHARED_VARIABLES.set_LOGDIR(logdir)
