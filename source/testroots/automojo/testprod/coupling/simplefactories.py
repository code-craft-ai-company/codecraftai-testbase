
from typing import Generator

from automojo import testbase

@testbase.factory.resource()
def create_blah(constraints={}) -> Generator[str, None, None]:
    yield "blah"