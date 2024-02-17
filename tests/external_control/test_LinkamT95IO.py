import pytest

from ExternalControl.LinkamT95.IO import LinkamT95Error, LinkamT95IO

LINKAMT95IO_PATH = "ExternalControl.LinkamT95.IO.LinkamT95SerialIO"
COMMAND = ""


def commandcheck(self, command):
    global COMMAND
    COMMAND = command


def test_Linkam(monkeypatch):
    monkeypatch.setattr(LINKAMT95IO_PATH + ".connect", commandcheck)
    monkeypatch.setattr(LINKAMT95IO_PATH + ".write", commandcheck)
    monkeypatch.setattr(LINKAMT95IO_PATH + ".query", lambda **args: b"aaaaaaaaaaaaaaa")

    target = LinkamT95IO()
    COMPORT = "COM3"
    target.connect(COMPORT)

    assert COMMAND == COMPORT

    target.start()
    assert COMMAND == "S"

    target.cool()
    assert COMMAND == "C"

    target.heat()
    assert COMMAND == "H"

    target.set_rate(100)
    assert COMMAND == "R110000"

    with pytest.raises(LinkamT95Error):
        target.set_rate(200)

    with pytest.raises(LinkamT95Error):
        target.set_rate(-1)

    target.set_lnp_speed(-1)
    assert COMMAND == "Pa0"

    target.set_lnp_speed(0)
    assert COMMAND == "P0"

    target.set_lnp_speed(1)
    assert COMMAND == "P1"

    target.set_lnp_speed(100)
    assert COMMAND == "PN"

    target.set_lnp_speed(99)
    assert COMMAND == "PN"

    with pytest.raises(LinkamT95Error):
        target.set_lnp_speed(101)

    target.set_limit_temperature(300)
    assert COMMAND == "L13000"

    target.set_limit_temperature(-70)
    assert COMMAND == "L1-700"

    with pytest.raises(LinkamT95Error):
        target.set_limit_temperature(-197)

    with pytest.raises(LinkamT95Error):
        target.set_limit_temperature(601)

    def dummy_query(self, command):
        return (
            b"\x10\x80"
            + (8 * 16 + 15).to_bytes(1, "big")
            + b"\x00\x00\x00"
            + int(3500).to_bytes(4, "big")
            + b"\x0d"
        )

    monkeypatch.setattr(LINKAMT95IO_PATH + ".query", dummy_query)
    state, T, lnp = target.read_status()

    assert state == LinkamT95IO.State.Heating
    assert T == 350
    assert lnp == 50

    def dummy_query(self, command):
        return (
            b"\x01\x80"
            + (8 * 16 + 30).to_bytes(1, "big")
            + b"\x00\x00\x00"
            + int(-1200).to_bytes(4, "big", signed=True)
            + b"\x0d"
        )

    monkeypatch.setattr(LINKAMT95IO_PATH + ".query", dummy_query)
    state, T, lnp = target.read_status()

    assert state == LinkamT95IO.State.Stopped
    assert T == -120
    assert lnp == 100
