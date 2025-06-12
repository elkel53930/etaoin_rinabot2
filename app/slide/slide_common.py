PORT = "11312"

from typing import NamedTuple

class SetImage(NamedTuple):
	filename: str

class Shutdown(NamedTuple):
    pass

