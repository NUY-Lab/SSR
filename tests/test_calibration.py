from pathlib import Path

from calibration import TMRCalibrationManager


def test_TMRCalibrationManager_1(tmp_path: Path):
    path = tmp_path / "calibration.txt"
    path.write_text(
        """T[K],R[Ohm]
1,100
2,200
3,300
4,400
5,500
"""
    )

    calibration = TMRCalibrationManager()
    calibration.set_own_calib_file(str(path))

    assert calibration.calibration(100) == 1
    assert calibration.calibration(250) == 2.5
    assert calibration.calibration(600) == 6
    assert calibration.calibration(50) == 0.5


def test_TMRCalibrationManager_2(tmp_path: Path):
    path = tmp_path / "calibration.txt"
    path.write_text(
        """T[K],R[Ohm]
1,100
4,200
9,300
16,400
25,500
"""
    )

    calibration = TMRCalibrationManager()
    calibration.set_own_calib_file(str(path))

    assert calibration.calibration(100) == 1
    assert calibration.calibration(250) == 6.5
    assert calibration.calibration(600) == 34
    assert calibration.calibration(50) == -0.5
