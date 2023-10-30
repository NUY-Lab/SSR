import math
from enum import Enum
from logging import getLogger
from typing import Tuple

from utility import MyException

from MAX303IO import MAX303SerialIO, MAX303Error


class MAX303Controller:
    def __init__(self) -> None:
        self.io = MAX303SerialIO()

    def connect(self, comport: str):
        self.io.connect(COMPORT=comport)

    def lamp_on(self):
        self.io.write("PW1")

    def lamp_off(self):
        self.io.write("PW0")  # MAX-303のランプを消す(p.6)

    def shutter_open(self):
        self.io.write("S1")

    def shutter_close(self):
        self.io.write("S0")
