from datetime import datetime
from io import StringIO
from logging import DEBUG, INFO, FileHandler, Formatter, StreamHandler, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

default_format = (
    "[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s"
)


def init_log(io: StringIO, dev=False):
    now = datetime.now()

    filename = f"./.ssr/log/{now.year}-{now.month}.log"
    fh = FileHandler(filename=filename, encoding="utf-8")
    fh.setLevel(INFO)
    fh.setFormatter(Formatter(default_format))

    rh = StreamHandler()
    rh.setLevel(INFO if not dev else DEBUG)
    rh.setFormatter(Formatter("%(message)s"))

    ui = StreamHandler(io)
    ui.setLevel(INFO)
    ui.setFormatter(Formatter(default_format))

    logger = getLogger()
    logger.setLevel(INFO if not dev else DEBUG)
    logger.addHandler(fh)
    logger.addHandler(rh)
    logger.addHandler(ui)


def init_user_log(path: Path):
    rfh = RotatingFileHandler(
        filename=path / "log.txt", encoding="utf8", maxBytes=1024 * 100
    )
    rfh.setLevel(INFO)
    rfh.setFormatter(Formatter(default_format))

    logger = getLogger()
    logger.addHandler(rfh)
