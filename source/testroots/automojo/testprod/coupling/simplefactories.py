
from typing import Generator

from automojo import testbase

@testbase.register.resource_factory()
def create_blah(constraints={}) -> Generator[str, None, None]:
    yield "blah"