from pathlib import Path

from log import setlog
from MAIN import main
from variables import init


def test_main_meas():
    # 初期化
    init(Path.cwd())
    setlog()

    main()
