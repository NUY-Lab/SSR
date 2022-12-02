import sys
import unittest
from secrets import token_bytes
from unittest import TestCase, mock

from requests import patch
from sympy import Dummy

sys.path.append("../")
import serial
from LinkamT95.Controller import (LinkamT95AutoController,
                                  LinkamT95ControllerError,
                                  LinkamT95ManualController)
from LinkamT95.IO import LinkamT95Error, LinkamT95IO, LinkamT95SerialIO
from measurement_manager_support import MeasurementState, MeasurementStep

COMMAND = ""


def commandcheck(self, command):
    global COMMAND
    COMMAND += command


class TestLinkamT95IO(unittest.TestCase):
    @mock.patch("LinkamT95.IO.LinkamT95SerialIO.connect", commandcheck)
    @mock.patch("LinkamT95.IO.LinkamT95SerialIO.write", commandcheck)
    def testLinkamController(self):
        global COMMAND
        controller = LinkamT95ManualController()
        controller.connect("COM6")
        self.assertEqual(COMMAND, "COM6")
        COMMAND = ""
        controller.run_program(130, 6, 90)
        self.assertIn("L11300", COMMAND)
        self.assertIn("R1600", COMMAND)
        self.assertIn("Pm0", COMMAND)
        self.assertIn("PK", COMMAND)

        COMMAND = ""
        controller.stop()
        self.assertIn("E", COMMAND)

        COMMAND = ""

        def dummy_query(self, command):

            return (
                b"\x10\x80"
                + (8 * 16 + 15).to_bytes(1, "big")
                + b"\x00\x00\x00"
                + int(3500).to_bytes(4, "big")
                + b"\x0d"
            )

        with mock.patch("LinkamT95.IO.LinkamT95SerialIO.query", dummy_query):
            has_reached_temperature, temperature = controller.get_status()
            self.assertEqual(has_reached_temperature, False)
            self.assertEqual(temperature, 350)

        def dummy_query(self, command):

            return (
                b"\x30\x80"
                + (8 * 16 + 15).to_bytes(1, "big")
                + b"\x00\x00\x00"
                + int(-1000).to_bytes(4, "big", signed=True)
                + b"\x0d"
            )

        with mock.patch("LinkamT95.IO.LinkamT95SerialIO.query", dummy_query):
            controller.run_program(-100, 1, 10)
            has_reached_temperature, temperature = controller.get_status()
            self.assertEqual(has_reached_temperature, True)
            self.assertEqual(temperature, -100)


dummy_has_reached_target_temperature = True
from datetime import datetime

import freezegun

OUTPUT=""
class TestLinkamT95AutoController(unittest.TestCase):
    class DummyController(mock.MagicMock):
        def connect(self, COMPORT: str) -> None:
            pass

        def run_program(
            self, temperature: int, temp_per_min: int, lnp_speed: int
        ) -> None:
            global OUTPUT
            OUTPUT=f"{temperature}"

        def get_status(self):
            global dummy_has_reached_target_temperature
            return (dummy_has_reached_target_temperature, 100)

        def stop(self):
            pass

    # @mock.patch(
    #     "LinkamT95.Controller.LinkamT95AutoController._LinkamT95AutoController__controller",
    #     DummyCOntroller,
    # )
    def test_auto_controller(self):
        measurementState = MeasurementState()
        measurementState.current_step = MeasurementStep.MEASURING
        controller = LinkamT95AutoController()
        controller._LinkamT95AutoController__controller = self.DummyController()
        controller.add_sequence(100, 0, 10, 10)
        controller.add_sequence(200, 0, 10, 10)
        self.assertEqual(
            controller._LinkamT95AutoController__update(measurementState), True
        )
        self.assertEqual(
            controller._LinkamT95AutoController__update(measurementState), True
        )
        controller._LinkamT95AutoController__update(measurementState)
        # print(controller._LinkamT95AutoController__timer.is_completed())
        self.assertEqual(
            controller._LinkamT95AutoController__update(measurementState), False
        )

        measurementState = MeasurementState()
        measurementState.current_step = MeasurementStep.MEASURING
        controller = LinkamT95AutoController()
        controller._LinkamT95AutoController__controller = self.DummyController()
        controller.add_sequence(100, 0, 10, 10)
        global dummy_has_reached_target_temperature
        dummy_has_reached_target_temperature = False
        for i in range(3):
            self.assertEqual(
                controller._LinkamT95AutoController__update(measurementState), True
            )
        dummy_has_reached_target_temperature = True
        controller._LinkamT95AutoController__update(measurementState)
        self.assertEqual(
            controller._LinkamT95AutoController__update(measurementState), False
        )

        #途中でMeasurementStateが変わったときに終了できるか
        measurementState = MeasurementState()
        measurementState.current_step = MeasurementStep.MEASURING
        controller = LinkamT95AutoController()
        controller._LinkamT95AutoController__controller = self.DummyController()
        controller.add_sequence(100, 0, 10, 10)
        dummy_has_reached_target_temperature = False
        for i in range(3):
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
        measurementState.current_step = MeasurementStep.FINISH_MEASURE
        self.assertEqual(controller._LinkamT95AutoController__update(measurementState), False)
        self.assertEqual(controller._LinkamT95AutoController__update(measurementState), False)


        #温度到達してから設定時間経過したら次へ進めるかどうか
        measurementState = MeasurementState()
        measurementState.current_step = MeasurementStep.MEASURING
        controller = LinkamT95AutoController()
        controller._LinkamT95AutoController__controller = self.DummyController()
        with freezegun.freeze_time('2015-10-21 00:00:00') as freeze_datetime:
            controller.add_sequence(100, 5, 10, 10)
            controller.add_sequence(200, 5, 10, 10)
            dummy_has_reached_target_temperature = True
            for i in range(3):
                self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
            self.assertEqual(OUTPUT, "100")
            
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
        with freezegun.freeze_time('2015-10-21 00:04:03') as freeze_datetime:           
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
        with freezegun.freeze_time('2015-10-21 00:05:03') as freeze_datetime:           
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
            self.assertEqual(OUTPUT, "200")

            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), True)
        with freezegun.freeze_time('2015-10-21 00:10:19') as freeze_datetime:           
            self.assertEqual(controller._LinkamT95AutoController__update(measurementState), False)
        


