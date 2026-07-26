"""
    .. module:: ccai.testbase.sequencing.sequencermodulescope
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for sequencermodulescope.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Type, TYPE_CHECKING


import os

from types import TracebackType

from ccai.errors.xtraceback import create_traceback_detail, format_traceback_detail
from ccai.errors.exceptions import SkipError

from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from ccai.testbase.results.recorders.resultrecorder import ResultRecorder
from ccai.testbase.sequencing.sequencerscopebase import SequencerScopeBase


logger = getEnhancedLogger()


if TYPE_CHECKING:
    from ccai.testbase.sequencing.testsequencer import TestSequencer


class SequencerModuleScope(SequencerScopeBase):
    """
        Context manager that manages the lifetime of a module level scope.
    """
    def __init__(self, sequencer: "TestSequencer", recorder: ResultRecorder, scope_name: str, **kwargs):
        super().__init__(sequencer, recorder)

        self._scope_name = scope_name
        self._scope_args = kwargs
        self._scope_id = None
        self._parent_scope_id = None
        self._scope_node = self._sequencer.find_treenode_for_scope(scope_name)
        return

    def __enter__(self):
        self._parent_scope_id, self._scope_id = self._sequencer.scope_id_create(self._scope_name)
        try:
            result = self._sequencer.create_test_result_container(self._scope_id, self._scope_name, parent_inst=self._parent_scope_id)
            self._recorder.record(result)
        except BaseException:
            # If __enter__ raises, Python never calls __exit__, so the scope
            # id pushed above would be left on the stack and every outer
            # scope's pop would fail its name check, burying the real error.
            # Pop what we pushed and let the true failure surface.
            self._sequencer.scope_id_pop(self._scope_name)
            raise
        logger.info("MODULE ENTER: {}, {}".format(self._scope_name, self._scope_id))
        return self

    def __exit__(self, ex_type: Type, ex_inst: BaseException, ex_tb: TracebackType) -> bool:
        handled = False

        if ex_type is not None:

            if issubclass(ex_type, SkipError):
                self._mark_descendants_skipped(self._scope_node, self._scope_id, ex_inst.reason, ex_inst.bug)
            else:
                tb_detail = create_traceback_detail(ex_inst)
                self._mark_descendants_as_error(self._scope_node,  self._scope_id, tb_detail)

                # If an exceptions was thrown in this context, it means
                # that the exception occured during the setup for this
                # module, this means we need to mark all descendant tests
                # as error'd due to a setup failure.
                errmsg_lines = [
                    "Exception raises setting up scope='{}'".format(self._scope_name)
                ]
                errmsg_lines.extend(format_traceback_detail(tb_detail))
                errmsg = os.linesep.join(errmsg_lines)
                logger.error(errmsg)
            
            handled = True

        self._scope_node.finalize()
        self._sequencer.scope_id_pop(self._scope_name)
        logger.info("MODULE EXIT: {}, {}".format(self._scope_name, self._scope_id))

        return handled
