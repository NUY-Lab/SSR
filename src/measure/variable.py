"""共有度の高い変数を置いておく"""
from pathlib import Path

ROOTDIR = Path.cwd()
SSRDIR = ROOTDIR / ".ssr"
TMPDIR = SSRDIR / "tmp"
LOGDIR = SSRDIR / "log"
SHAREDDIR = SSRDIR / "shared"


def init():
    # フォルダがなかったら作る
    if not SSRDIR.is_dir():
        SSRDIR.mkdir()
    if not TMPDIR.is_dir():
        TMPDIR.mkdir()
    if not LOGDIR.is_dir():
        LOGDIR.mkdir()
    if not SHAREDDIR.is_dir():
        SHAREDDIR.mkdir()
