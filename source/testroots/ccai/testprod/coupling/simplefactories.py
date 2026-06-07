
from typing import Generator

from ccai import testbase

@testbase.register.resource_factory()
def create_blah(constraints={}) -> Generator[str, None, None]:
    yield "blah"