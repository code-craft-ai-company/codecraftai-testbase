"""
    .. module:: automojo.testbase.results.model.jobcontainer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for jobcontainer.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.results.model.resulttype import ResultType
from automojo.testbase.results.model.resultcontainer import ResultContainer

class JobContainer(ResultContainer):
    """
        The :class:`JobContainer` instances are container nodes that are used to link result nodes in the
        result tree.  The :class:`JobContainer` node is the base node for the tree.
    """
    def __init__(self, inst_id: str, name: str):
        """
            Creates an instance of a result container.

            :param inst_id: The unique identifier to link this result container with its children.
            :param name: The name of the result container.
        """
        super().__init__(inst_id, name, ResultType.JOB, parent_inst=None)
        return
