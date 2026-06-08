
from ccai import testbase


from ccai.testprod.coupling.simplefactories import create_blah


testbase.originate.parameter(create_blah, identifier='blah', constraints={"message": "something"})
