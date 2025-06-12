PORT = 11310

from typing import NamedTuple

class SetPositions(NamedTuple):
    j1: float
    j2: float
    j3: float

class Shutdown(NamedTuple):
    pass

