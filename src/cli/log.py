from datetime import datetime
from logging import INFO, FileHandler, Formatter, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

default_format = (
    "[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s"
)


def init_log():
    now = datetime.now()

    filename = f"./log/{now.year}-{now.month}.log"
    fh = FileHandler(filename=filename, encoding="utf-8")
    fh.setLevel(INFO)
    fh.setFormatter(Formatter(default_format))

    rh = RichHandler(rich_tracebacks=True)
    rh.setLevel(INFO)
    rh.setFormatter(Formatter("%(message)s"))

    logger = getLogger()
    logger.setLevel(INFO)
    logger.addHandler(fh)
    logger.addHandler(rh)


def init_user_log(path: Path):
    rfh = RotatingFileHandler(
        filename=path / "log.txt", encoding="utf8", maxBytes=1024 * 100
    )
    rfh.setLevel(INFO)
    rfh.setFormatter(Formatter(default_format))

    logger = getLogger()
    logger.addHandler(rfh)