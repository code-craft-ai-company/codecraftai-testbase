"""
    .. module:: ccai.testbase.sequencing.sequencertestsetupscope
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for sequencertestsetupscope.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import TYPE_CHECKING

import os

from ccai.errors.xtraceback import create_traceback_detail, format_traceback_detail
from ccai.errors.exceptions import SkipError

from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from ccai.testbase.results.recorders.resultrecorder import ResultRecorder
from ccai.testbase.sequencing.sequencerscopebase import SequencerScopeBase

logger = getEnhancedLogger()


if TYPE_CHECKING:
    from ccai.testbase.sequencing.testsequencer import TestSequencer


class SequencerTestSetupScope(SequencerScopeBase):
    """
        Context manager that manages setup operations for a test scope.
    """

    def __init__(self, sequencer: "TestSequencer", recorder: ResultRecorder, test_name: str, **kwargs):
        super().__init__(sequencer, recorder)

        self._sequencer = sequencer
        self._recorder = recorder
        self._test_name = test_name
        self._scope_name = "setup:{}".format(test_name)
        self._scope_args = kwargs
        self._scope_id = None
        self._parent_scope_id = None
        self._test_scope_node = self._sequencer.find_treenode_for_scope(test_name)
        return

    def __enter__(self):
        self._parent_scope_id, self._scope_id = self._sequencer.scope_id_create(self._scope_name)
        logger.info("TEST SETUP ENTER: {}, {}".format(self._scope_name, self._scope_id))
        return self

    def __exit__(self, ex_type, ex_inst, ex_tb):
        handled = False

        if ex_type is not None:

            if issubclass(ex_type, SkipError):
                self._mark_test_as_skip(self._test_scope_node, self._scope_id, ex_inst.reason, ex_inst.bug)
            else:
                tb_detail = create_traceback_detail(ex_inst)
                self._mark_test_as_error(self._test_scope_node,  self._scope_id, tb_detail)

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


        self._test_scope_node.finalize()
        self._sequencer.scope_id_pop(self._scope_name)
        logger.info("TEST SETUP EXIT: {}, {}".format(self._scope_name, self._scope_id))
        return handled
