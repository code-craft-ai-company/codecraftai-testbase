"""
    .. module:: automojo.testbase.sequencing.sequencerscopebase
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for sequencerscopebase.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import TYPE_CHECKING

import uuid

from automojo.errors.xtraceback import TracebackDetail

from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from automojo.testbase.results.recorders.resultrecorder import ResultRecorder
from automojo.testbase.testgroup import TestGroup
from automojo.testbase.testref import TestRef

if TYPE_CHECKING:
    from automojo.testbase.sequencing.testsequencer import TestSequencer

logger = getEnhancedLogger()

class SequencerScopeBase:
    """
        Base context manager for all sequencer scope implementations.
    """

    def __init__(self, sequencer: "TestSequencer", recorder: ResultRecorder):
        super().__init__()

        self._sequencer = sequencer
        self._recorder = recorder
        return

    def _mark_descendants_as_error(self, cursor, cursor_id, tbdetail):

        for chkey in cursor.children:
            child = cursor.children[chkey]
            if not child.finalized:
                if isinstance(child, TestRef):
                    self._mark_test_as_error(child, cursor_id, tbdetail)
                elif isinstance(child, TestGroup):
                    scope_id = str(uuid.uuid4())
                    scope_name = child.scope_name
                    result = self._sequencer.create_test_result_container(scope_id, scope_name, parent_inst=cursor_id)
                    self._recorder.record(result)
                    self._mark_descendants_as_error(child, scope_id, tbdetail)

        return

    def _mark_descendants_skipped(self, cursor, cursor_id, reason, bug):

        for chkey in cursor.children:
            child = cursor.children[chkey]
            if not child.finalized:
                if isinstance(child, TestRef):
                    self._mark_test_as_skip(child, cursor_id, reason, bug)
                elif isinstance(child, TestGroup):
                    scope_id = str(uuid.uuid4())
                    scope_name = child.scope_name
                    result = self._sequencer.create_test_result_container(scope_id, scope_name, parent_inst=cursor_id)
                    self._recorder.record(result)
                    self._mark_descendants_skipped(child, scope_id, reason, bug)

        return

    def _mark_test_as_error(self, testref: TestRef, parent_id: str, tbdetail: TracebackDetail):
        test_id = str(uuid.uuid4())
        result = self._sequencer.create_test_result_node(test_id, testref.name, testref.monikers, testref.pivots, parent_inst=parent_id)
        result.add_error(tbdetail)
        result.finalize()
        self._recorder.record(result)
        return

    def _mark_test_as_skip(self, testref: TestRef, parent_id: str, reason: str, bug: str):
        test_id = str(uuid.uuid4())
        result = self._sequencer.create_test_result_node(test_id, testref.name, testref.monikers, testref.pivots, parent_inst=parent_id)
        result.mark_skip(reason, bug)
        result.finalize()
        self._recorder.record(result)
        return