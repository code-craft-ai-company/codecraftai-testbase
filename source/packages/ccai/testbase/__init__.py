"""
    .. module:: ccai.testbase
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testbase.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""




__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.xmodules.xlogging.enhancedloggers import EnhancedLogger, getEnhancedLogger

logger: EnhancedLogger = getEnhancedLogger()

from ccai.testbase.declaration import attachments as attach
from ccai.testbase.declaration import registrations as register
from ccai.testbase.declaration import originations as originate

from ccai.testbase.declaration.parameterization import (
    parametrize, ParametrizedCaseError
)


from ccai.testbase.verification import (
    raises,
    assert_dict_response_has_keys,
    assert_dict_response_has_paths,
    assert_equal,
    assert_expression,
    assert_false,
    assert_greater,
    assert_lessthan,
    assert_list_length,
    assert_list_length_greater,
    assert_not_equal,
    assert_true,
    assert_type
)

from ccai.testbase.markers import (
    mark_categories,
    mark_keywords,
    mark_priority,
    mark_descendent_categories,
    mark_descendent_keywords,
    mark_descendent_priority
)

from ccai.testbase.results.model.taskingresult import (
    verify_tasking_results
)

from ccai.testbase.constraints import (
    Constraints,
    ConstraintsCatalog,
    FeatureConstraints
)
