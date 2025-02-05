
from automojo import testbase


from automojo.testprod.coupling.simplefactories import create_blah


testbase.originate.originate_parameter(create_blah, identifier='blah', constraints={"message": "something"})
