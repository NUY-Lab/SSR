from unittest import mock

from ExternalControl.LinkamT95.Controller import (
    LinkamT95AutoController,
    LinkamT95ManualController,
)
from measurement_manager_support import MeasurementState, MeasurementStep

LINKAMT95IO_PATH = "ExternalControl.LinkamT95.IO.LinkamT95SerialIO"
COMMAND = ""


def commandcheck(self, command):
    global COMMAND
    COMMAND += command


def test_LinkamController(monkeypatch):
    global COMMAND

    monkeypatch.setattr(LINKAMT95IO_PATH + ".connect", commandcheck)
    monkeypatch.setattr(LINKAMT95IO_PATH + ".write", commandcheck)

    controller = LinkamT95ManualController()
    controller.connect("COM6")
    assert COMMAND == "COM6"

    COMMAND = ""
    controller.run_program(130, 6, 90)
    assert "L11300" in COMMAND
    assert "R1600" in COMMAND
    assert "Pm0" in COMMAND
    assert "PK" in COMMAND

    COMMAND = ""
    controller.stop()
    assert "E" in COMMAND

    COMMAND = ""

    def dummy_query(self, command):
        return (
            b"\x10\x80"
            + (8 * 16 + 15).to_bytes(1, "big")
            + b"\x00\x00\x00"
            + int(3500).to_bytes(4, "big")
            + b"\x0d"
        )

    monkeypatch.setattr(LINKAMT95IO_PATH + ".query", dummy_query)
    has_reached_temperature, temperature = controller.get_status()

    assert has_reached_temperature is False
    assert temperature == 350

    def dummy_query(self, command):
        return (
            b"\x30\x80"
            + (8 * 16 + 15).to_bytes(1, "big")
            + b"\x00\x00\x00"
            + int(-1000).to_bytes(4, "big", signed=True)
            + b"\x0d"
        )

    monkeypatch.setattr(LINKAMT95IO_PATH + ".query", dummy_query)
    controller.run_program(-100, 1, 10)
    has_reached_temperature, temperature = controller.get_status()

    assert has_reached_temperature is True
    assert temperature == -100


dummy_has_reached_target_temperature = True


OUTPUT = ""


class DummyController(mock.MagicMock):
    def connect(self, COMPORT: str) -> None:
        pass

    def run_program(self, temperature: int, temp_per_min: int, lnp_speed: int) -> None:
        global OUTPUT
        OUTPUT = f"{temperature}"

    def get_status(self):
        global dummy_has_reached_target_temperature
        return (dummy_has_reached_target_temperature, 100)

    def stop(self):
        pass


def test_auto_controller_1():
    measurementState = MeasurementState()
    measurementState.current_step = MeasurementStep.MEASURING
    controller = LinkamT95AutoController()
    controller._LinkamT95AutoController__controller = DummyController()
    controller.add_sequence(100, 0, 10, 10)
    controller.add_sequence(200, 0, 10, 10)

    assert controller._LinkamT95AutoController__update(measurementState) is True
    assert controller._LinkamT95AutoController__update(measurementState) is True

    controller._LinkamT95AutoController__update(measurementState)

    assert controller._LinkamT95AutoController__update(measurementState) is False


def test_auto_controller_2():
    global dummy_has_reached_target_temperature

    measurementState = MeasurementState()
    measurementState.current_step = MeasurementStep.MEASURING
    controller = LinkamT95AutoController()
    controller._LinkamT95AutoController__controller = DummyController()
    controller.add_sequence(100, 0, 10, 10)

    dummy_has_reached_target_temperature = False

    assert controller._LinkamT95AutoController__update(measurementState) is True
    assert controller._LinkamT95AutoController__update(measurementState) is True
    assert controller._LinkamT95AutoController__update(measurementState) is True

    dummy_has_reached_target_temperature = True
    controller._LinkamT95AutoController__update(measurementState)

    assert controller._LinkamT95AutoController__update(measurementState) is False


def test_auto_controller_3():
    global dummy_has_reached_target_temperature

    # 途中でMeasurementStateが変わったときに終了できるか
    measurementState = MeasurementState()
    measurementState.current_step = MeasurementStep.MEASURING
    controller = LinkamT95AutoController()
    controller._LinkamT95AutoController__controller = DummyController()
    controller.add_sequence(100, 0, 10, 10)
    dummy_has_reached_target_temperature = False

    assert controller._LinkamT95AutoController__update(measurementState) is True
    assert controller._LinkamT95AutoController__update(measurementState) is True
    assert controller._LinkamT95AutoController__update(measurementState) is True

    measurementState.current_step = MeasurementStep.FINISH_MEASURE

    assert controller._LinkamT95AutoController__update(measurementState) is False
    assert controller._LinkamT95AutoController__update(measurementState) is False


def test_auto_controller():
    global dummy_has_reached_target_temperature

    import freezegun

    # 温度到達してから設定時間経過したら次へ進めるかどうか
    measurementState = MeasurementState()
    measurementState.current_step = MeasurementStep.MEASURING
    controller = LinkamT95AutoController()
    controller._LinkamT95AutoController__controller = DummyController()

    with freezegun.freeze_time("2015-10-21 00:00:00"):
        controller.add_sequence(100, 5, 10, 10)
        controller.add_sequence(200, 5, 10, 10)
        dummy_has_reached_target_temperature = True

        assert controller._LinkamT95AutoController__update(measurementState) is True
        assert controller._LinkamT95AutoController__update(measurementState) is True
        assert controller._LinkamT95AutoController__update(measurementState) is True

        assert OUTPUT == "100"
        assert controller._LinkamT95AutoController__update(measurementState) is True
        assert controller._LinkamT95AutoController__update(measurementState) is True

    with freezegun.freeze_time("2015-10-21 00:04:03"):
        assert controller._LinkamT95AutoController__update(measurementState) is True

    with freezegun.freeze_time("2015-10-21 00:05:03"):
        assert controller._LinkamT95AutoController__update(measurementState) is True
        assert OUTPUT == "200"
        assert controller._LinkamT95AutoController__update(measurementState) is True
        assert controller._LinkamT95AutoController__update(measurementState) is True

    with freezegun.freeze_time("2015-10-21 00:10:19"):
        assert controller._LinkamT95AutoController__update(measurementState) is False
