import freezegun

from instrument.LinkamT95.controller import (
    LinkamT95AutoController,
    LinkamT95ManualController,
)
from measure.measurement import State

COMMAND = ""


def commandcheck(self, command):
    global COMMAND
    COMMAND += command


def test_LinkamController(monkeypatch):
    global COMMAND
    monkeypatch.setattr(
        "instrument.LinkamT95.io.LinkamT95SerialIO.connect", commandcheck
    )
    monkeypatch.setattr("instrument.LinkamT95.io.LinkamT95SerialIO.write", commandcheck)

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

    assert COMMAND == "E"

    COMMAND = ""

    def dummy_query(self, command):
        return (
            b"\x10\x80"
            + (8 * 16 + 15).to_bytes(1, "big")
            + b"\x00\x00\x00"
            + int(3500).to_bytes(4, "big")
            + b"\x0d"
        )

    monkeypatch.setattr("instrument.LinkamT95.io.LinkamT95SerialIO.query", dummy_query)
    has_reached_temperature, temperature = controller.get_status()

    assert has_reached_temperature == False
    assert temperature == 350

    def dummy_query(self, command):
        return (
            b"\x30\x80"
            + (8 * 16 + 15).to_bytes(1, "big")
            + b"\x00\x00\x00"
            + int(-1000).to_bytes(4, "big", signed=True)
            + b"\x0d"
        )

    monkeypatch.setattr("instrument.LinkamT95.io.LinkamT95SerialIO.query", dummy_query)
    controller.run_program(-100, 1, 10)
    has_reached_temperature, temperature = controller.get_status()

    assert has_reached_temperature == True
    assert temperature == -100


dummy_has_reached_target_temperature = True
OUTPUT = ""


class DummyController:
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


def test_LinkamAutoController(monkeypatch):
    monkeypatch.setattr("instrument.LinkamT95.controller._state", lambda: State.UPDATE)
    controller = LinkamT95AutoController()
    controller._controller = DummyController()
    controller.add_sequence(100, 0, 10, 10)
    controller.add_sequence(200, 0, 10, 10)

    assert controller._update() == True
    assert controller._update() == True

    controller._update()

    assert controller._update() == False

    monkeypatch.setattr("instrument.LinkamT95.controller._state", lambda: State.UPDATE)
    controller = LinkamT95AutoController()
    controller._controller = DummyController()
    controller.add_sequence(100, 0, 10, 10)
    global dummy_has_reached_target_temperature
    dummy_has_reached_target_temperature = False

    for _ in range(3):
        assert controller._update() == True

    dummy_has_reached_target_temperature = True
    controller._update()

    assert controller._update() == False

    # 途中でMeasurementStateが変わったときに終了できるか
    monkeypatch.setattr("instrument.LinkamT95.controller._state", lambda: State.UPDATE)
    controller = LinkamT95AutoController()
    controller._controller = DummyController()
    controller.add_sequence(100, 0, 10, 10)
    dummy_has_reached_target_temperature = False

    for _ in range(3):
        assert controller._update() == True

    monkeypatch.setattr(
        "instrument.LinkamT95.controller._state", lambda: State.FINISH_MEASURE
    )

    assert controller._update() == False
    assert controller._update() == False

    # 温度到達してから設定時間経過したら次へ進めるかどうか
    monkeypatch.setattr("instrument.LinkamT95.controller._state", lambda: State.UPDATE)
    controller = LinkamT95AutoController()
    controller._controller = DummyController()
    with freezegun.freeze_time("2015-10-21 00:00:00"):
        controller.add_sequence(100, 5, 10, 10)
        controller.add_sequence(200, 5, 10, 10)
        dummy_has_reached_target_temperature = True

        for i in range(3):
            assert controller._update() == True
        assert OUTPUT == "100"
        assert controller._update() == True
        assert controller._update() == True

    with freezegun.freeze_time("2015-10-21 00:04:03"):
        assert controller._update() == True

    with freezegun.freeze_time("2015-10-21 00:05:03"):
        assert controller._update() == True
        assert OUTPUT == "200"
        assert controller._update() == True
        assert controller._update() == True

    with freezegun.freeze_time("2015-10-21 00:10:19"):
        assert controller._update() == False
