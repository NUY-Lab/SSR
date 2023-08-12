"""ログ出力関係"""
import json
from datetime import datetime
from logging import INFO, Filter, Formatter, LogRecord, config, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from variables import SHARED_VARIABLES

logger = getLogger(f"SSR.{__name__}")


def log(text: str) -> None:
    """ユーザー用に簡易ログ出力を提供"""
    logger.info(text)


def setlog() -> None:
    """ログファイルのセット"""

    with (SHARED_VARIABLES.SSR_SCRIPTSDIR / "log_config.json").open(
        mode="r", encoding="utf-8"
    ) as f:
        conf = json.load(f)

        now = datetime.now()

        # 月ごとに新しいファイルにログを書き出す
        logfilepath=str(
            SHARED_VARIABLES.LOGDIR / f"{now.year}-{now.month}.log"
        )
        conf["handlers"]["sharedFileHandler"]["filename"] = logfilepath
        conf["handlers"]["SSRDebugFileHandler"]["filename"] = logfilepath
        conf["filters"]["onlyDebug_filter"]["()"]=OnlyDEBUGFileter
        config.dictConfig(conf)


class OnlyDEBUGFileter(Filter):
    def __init__(self, name: str = "") -> None:
        super().__init__(name)
    def filter(self, record: LogRecord) -> bool:
        return record.levelname == "DEBUG"

def set_user_log(path: str) -> None:
    """ユーザーフォルダ内にもログファイル書き出し"""
    path = Path(path) / "log.txt"
    handler = RotatingFileHandler(
        filename=path,
        encoding="utf-8",
        maxBytes=1024 * 100,
    )
    fmt = Formatter(
        "[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s"
    )

    handler.setLevel(INFO)
    handler.setFormatter(fmt)
    getLogger().addHandler(handler)
