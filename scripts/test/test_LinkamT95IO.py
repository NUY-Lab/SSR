import sys
import unittest
from secrets import token_bytes
from unittest import TestCase, mock

from requests import patch

sys.path.append("../")
import serial
from ExternalControl.LinkamT95.IO import LinkamT95Error, LinkamT95IO, LinkamT95SerialIO

COMMAND = ""


def querycommand(self, command):
    return b"aaaaaaaaaaaaaaa"


def commandcheck(self, command):
    global COMMAND
    COMMAND = command


class TestLinkamT95IO(unittest.TestCase):
    @mock.patch("LinkamT95.IO.LinkamT95SerialIO.connect", commandcheck)
    @mock.patch("LinkamT95.IO.LinkamT95SerialIO.write", commandcheck)
    @mock.patch("LinkamT95.IO.LinkamT95SerialIO.query", querycommand)
    def test_Linkam(self):
        target = LinkamT95IO()
        COMPORT = "COM3"
        target.connect(COMPORT)
        self.assertEqual(COMMAND, COMPORT)

        target.start()
        self.assertEqual(COMMAND, "S")
        target.cool()
        self.assertEqual(COMMAND, "C")
        target.heat()
        self.assertEqual(COMMAND, "H")
        target.set_rate(100)
        self.assertEqual(COMMAND, "R110000")
        with self.assertRaises(LinkamT95Error):
            target.set_rate(200)
        with self.assertRaises(LinkamT95Error):
            target.set_rate(-1)
        target.set_lnp_speed(-1)
        self.assertEqual(COMMAND, "Pa0")
        target.set_lnp_speed(0)
        self.assertEqual(COMMAND, "P0")
        target.set_lnp_speed(1)
        self.assertEqual(COMMAND, "P1")
        target.set_lnp_speed(100)
        self.assertEqual(COMMAND, "PN")
        target.set_lnp_speed(99)
        self.assertEqual(COMMAND, "PN")
        with self.assertRaises(LinkamT95Error):
            target.set_lnp_speed(101)

        target.set_limit_temperature(300)
        self.assertEqual(COMMAND, "L13000")
        target.set_limit_temperature(-70)
        self.assertEqual(COMMAND, "L1-700")

        with self.assertRaises(LinkamT95Error):
            target.set_limit_temperature(-197)
        with self.assertRaises(LinkamT95Error):
            target.set_limit_temperature(601)

        def dummy_query(self, command):
            return (
                b"\x10\x80"
                + (8 * 16 + 15).to_bytes(1, "big")
                + b"\x00\x00\x00"
                + int(3500).to_bytes(4, "big")
                + b"\x0d"
            )

        with mock.patch("LinkamT95.IO.LinkamT95SerialIO.query", dummy_query):
            state, T, lnp = target.read_status()
            self.assertEqual(state, LinkamT95IO.State.Heating)
            self.assertEqual(T, 350)
            self.assertEqual(lnp, 50)

        def dummy_query(self, command):
            return (
                b"\x01\x80"
                + (8 * 16 + 30).to_bytes(1, "big")
                + b"\x00\x00\x00"
                + int(-1200).to_bytes(4, "big", signed=True)
                + b"\x0d"
            )

        with mock.patch("LinkamT95.IO.LinkamT95SerialIO.query", dummy_query):
            state, T, lnp = target.read_status()
            self.assertEqual(state, LinkamT95IO.State.Stopped)
            self.assertEqual(T, -120)
            self.assertEqual(lnp, 100)


if __name__ == "__main__":
    unittest.main()
    # ser = serial.Serial()
