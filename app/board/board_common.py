PORT = "11311"

from typing import NamedTuple

class SetExp(NamedTuple):
    exp: str

class Shutdown(NamedTuple):
    pass