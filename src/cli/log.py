from datetime import datetime
from logging import DEBUG, INFO, FileHandler, Formatter, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from .rich import console

default_format = (
    "[%(asctime)s] [%(levelname)8s] [%(filename)s:%(lineno)s %(funcName)s]  %(message)s"
)


def init_log(dev=False):
    now = datetime.now()

    filename = f"./.ssr/log/{now.year}-{now.month}.log"
    fh = FileHandler(filename=filename, encoding="utf-8")
    fh.setLevel(INFO)
    fh.setFormatter(Formatter(default_format))

    rh = RichHandler(rich_tracebacks=True, console=console)
    rh.setLevel(INFO if not dev else DEBUG)
    rh.setFormatter(Formatter("%(message)s"))

    logger = getLogger()
    logger.setLevel(INFO if not dev else DEBUG)
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
