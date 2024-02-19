from pathlib import Path

import pytest

from variables import SHARED_VARIABLES, init


def test_shared_vars(tmp_path: Path):
    with pytest.raises(ValueError):
        SHARED_VARIABLES.SSR_HOMEDIR

    with pytest.raises(ValueError):
        SHARED_VARIABLES.SSR_SCRIPTSDIR

    with pytest.raises(ValueError):
        SHARED_VARIABLES.TEMPDIR

    with pytest.raises(ValueError):
        SHARED_VARIABLES.SETTINGDIR

    with pytest.raises(ValueError):
        SHARED_VARIABLES.LOGDIR

    init(tmp_path)

    temp = tmp_path / "temp"
    setting = tmp_path / "shared_settings"
    log = tmp_path / "log"

    assert SHARED_VARIABLES.SSR_HOMEDIR == tmp_path
    assert SHARED_VARIABLES.SSR_SCRIPTSDIR == tmp_path / "scripts"
    assert SHARED_VARIABLES.TEMPDIR == temp
    assert SHARED_VARIABLES.SETTINGDIR == setting
    assert SHARED_VARIABLES.LOGDIR == log

    assert temp.is_dir()
    assert setting.is_dir()
    assert log.is_dir()
