"""
    .. module:: automojo.testbase.results.model.progressaggregator
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for progress aggregation across distributed tasks.

    .. moduleauthor:: AutomationX
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Dict, List, Optional, Union

import threading

from datetime import datetime

from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progresstype import ProgressType
from automojo.testbase.results.model.progressinfo import ProgressInfo
from automojo.testbase.results.model.nestedprogressinfo import NestedProgressInfo


class ProgressAggregator:
    """
        Aggregates progress information from multiple distributed tasks into a
        unified hierarchical view.

        The :class:`ProgressAggregator` provides functionality for:

        1. **Nested Progress Tracking**: Maintains a tree structure of progress
           indicators where child progress can be linked to parent progress.

        2. **Progress Aggregation**: Computes aggregate progress metrics from
           child progress indicators, including:
           - Overall completion percentage
           - Aggregate status (based on child statuses)
           - Count of completed, running, and pending children

        3. **Thread Safety**: All operations are protected by a lock to ensure
           safe concurrent access from multiple threads.

        The aggregator is designed to work with distributed test execution where
        multiple workers report progress independently. It consolidates these
        reports into a coherent view of overall progress.

        Example Usage::

            aggregator = ProgressAggregator()

            # Register a parent progress indicator
            parent_progress = NestedProgressInfo(
                id="suite-123",
                category="test-suite",
                moniker="Integration Tests",
                ptype=ProgressType.NumericRange,
                range_min="0",
                range_max="100",
                position="0",
                status=ProgressCode.Running,
                when=datetime.now(),
                parent_id=None,
                depth=0
            )
            aggregator.register_progress(parent_progress)

            # Register child progress indicators
            child_progress = NestedProgressInfo(
                id="test-456",
                category="test",
                moniker="test_login",
                ptype=ProgressType.Sequential,
                range_min="0",
                range_max="1",
                position="1",
                status=ProgressCode.Completed,
                when=datetime.now(),
                parent_id="suite-123",
                depth=1
            )
            aggregator.register_progress(child_progress)

            # Get aggregated progress for the parent
            aggregated = aggregator.get_aggregated_progress("suite-123")
    """

    def __init__(self):
        """
            Initializes a new ProgressAggregator instance.

            :returns: None
        """
        # Dictionary mapping progress IDs to NestedProgressInfo objects
        self._progress_tree: Dict[str, NestedProgressInfo] = {}

        # Dictionary mapping parent IDs to lists of child IDs for quick lookup
        self._parent_children_map: Dict[str, List[str]] = {}

        # Lock for thread-safe operations
        self._lock = threading.Lock()

    def register_progress(self, progress: Union[ProgressInfo, NestedProgressInfo]) -> NestedProgressInfo:
        """
            Registers a progress indicator with the aggregator.

            If the progress is a regular :class:`ProgressInfo`, it will be converted
            to a :class:`NestedProgressInfo`. If the progress has a parent_id, the
            parent-child relationship will be established.

            :param progress: The progress indicator to register. Can be either
                             a ProgressInfo or NestedProgressInfo instance.

            :returns: The registered NestedProgressInfo instance.

            :rtype: NestedProgressInfo
        """
        self._lock.acquire()
        try:
            # Convert to NestedProgressInfo if necessary
            if isinstance(progress, NestedProgressInfo):
                nested_progress = progress
            else:
                nested_progress = NestedProgressInfo.from_progress_info(progress)

            progress_id = nested_progress.id
            parent_id = nested_progress.parent_id

            # Update or add the progress in the tree
            if progress_id in self._progress_tree:
                # Update existing progress, preserving children_ids
                existing = self._progress_tree[progress_id]
                nested_progress.children_ids = existing.children_ids
            
            self._progress_tree[progress_id] = nested_progress

            # Establish parent-child relationship if parent exists
            if parent_id is not None:
                if parent_id not in self._parent_children_map:
                    self._parent_children_map[parent_id] = []
                
                if progress_id not in self._parent_children_map[parent_id]:
                    self._parent_children_map[parent_id].append(progress_id)

                # Update parent's children_ids if parent exists in tree
                if parent_id in self._progress_tree:
                    self._progress_tree[parent_id].add_child(progress_id)

            return nested_progress

        finally:
            self._lock.release()

    def update_progress(self, progress_id: str, position: str = None,
                        status: ProgressCode = None, data: dict = None) -> Optional[NestedProgressInfo]:
        """
            Updates an existing progress indicator.

            :param progress_id: The ID of the progress indicator to update.
            :param position: Optional new position value.
            :param status: Optional new status value.
            :param data: Optional new data dictionary.

            :returns: The updated NestedProgressInfo, or None if not found.

            :rtype: Optional[NestedProgressInfo]
        """
        self._lock.acquire()
        try:
            if progress_id not in self._progress_tree:
                return None

            progress = self._progress_tree[progress_id]

            if position is not None:
                progress.position = position
            if status is not None:
                progress.status = status
            if data is not None:
                progress.data = data

            progress.when = datetime.now()

            return progress

        finally:
            self._lock.release()

    def remove_progress(self, progress_id: str) -> Optional[NestedProgressInfo]:
        """
            Removes a progress indicator from the aggregator.

            This also removes the progress from its parent's children list and
            removes any child progress indicators recursively.

            :param progress_id: The ID of the progress indicator to remove.

            :returns: The removed NestedProgressInfo, or None if not found.

            :rtype: Optional[NestedProgressInfo]
        """
        self._lock.acquire()
        try:
            if progress_id not in self._progress_tree:
                return None

            progress = self._progress_tree[progress_id]
            parent_id = progress.parent_id

            # Remove from parent's children list
            if parent_id is not None:
                if parent_id in self._parent_children_map:
                    if progress_id in self._parent_children_map[parent_id]:
                        self._parent_children_map[parent_id].remove(progress_id)
                
                if parent_id in self._progress_tree:
                    self._progress_tree[parent_id].remove_child(progress_id)

            # Remove children recursively (collect IDs first to avoid modification during iteration)
            children_to_remove = list(progress.children_ids)
            for child_id in children_to_remove:
                self._remove_progress_unlocked(child_id)

            # Remove from parent_children_map
            if progress_id in self._parent_children_map:
                del self._parent_children_map[progress_id]

            # Remove from tree
            del self._progress_tree[progress_id]

            return progress

        finally:
            self._lock.release()

    def _remove_progress_unlocked(self, progress_id: str) -> None:
        """
            Internal method to remove progress without acquiring lock.
            Used for recursive removal of children.

            :param progress_id: The ID of the progress indicator to remove.

            :returns: None
        """
        if progress_id not in self._progress_tree:
            return

        progress = self._progress_tree[progress_id]

        # Remove children recursively
        children_to_remove = list(progress.children_ids)
        for child_id in children_to_remove:
            self._remove_progress_unlocked(child_id)

        # Remove from parent_children_map
        if progress_id in self._parent_children_map:
            del self._parent_children_map[progress_id]

        # Remove from tree
        del self._progress_tree[progress_id]

    def get_progress(self, progress_id: str) -> Optional[NestedProgressInfo]:
        """
            Retrieves a progress indicator by ID.

            :param progress_id: The ID of the progress indicator to retrieve.

            :returns: The NestedProgressInfo, or None if not found.

            :rtype: Optional[NestedProgressInfo]
        """
        self._lock.acquire()
        try:
            return self._progress_tree.get(progress_id)
        finally:
            self._lock.release()

    def get_children(self, parent_id: str) -> List[NestedProgressInfo]:
        """
            Retrieves all child progress indicators for a given parent.

            :param parent_id: The ID of the parent progress indicator.

            :returns: A list of child NestedProgressInfo objects.

            :rtype: List[NestedProgressInfo]
        """
        self._lock.acquire()
        try:
            children = []
            child_ids = self._parent_children_map.get(parent_id, [])
            for child_id in child_ids:
                if child_id in self._progress_tree:
                    children.append(self._progress_tree[child_id])
            return children
        finally:
            self._lock.release()

    def get_root_progress(self) -> List[NestedProgressInfo]:
        """
            Retrieves all root-level progress indicators (those without parents).

            :returns: A list of root-level NestedProgressInfo objects.

            :rtype: List[NestedProgressInfo]
        """
        self._lock.acquire()
        try:
            roots = []
            for progress in self._progress_tree.values():
                if progress.parent_id is None:
                    roots.append(progress)
            return roots
        finally:
            self._lock.release()

    def get_aggregated_progress(self, progress_id: str) -> Optional[dict]:
        """
            Computes aggregated progress metrics for a progress indicator and
            all its descendants.

            The aggregated metrics include:
            - total_children: Total number of descendant progress indicators
            - completed_count: Number of descendants with Completed status
            - running_count: Number of descendants with Running status
            - pending_count: Number of descendants with NotStarted status
            - errored_count: Number of descendants with Errored status
            - failed_count: Number of descendants with Failed status
            - paused_count: Number of descendants with Paused status
            - completion_percentage: Percentage of completed descendants
            - aggregate_status: Overall status based on child statuses

            :param progress_id: The ID of the progress indicator to aggregate.

            :returns: A dictionary containing aggregated metrics, or None if
                      the progress indicator is not found.

            :rtype: Optional[dict]
        """
        self._lock.acquire()
        try:
            if progress_id not in self._progress_tree:
                return None

            progress = self._progress_tree[progress_id]

            # Collect all descendant statuses
            status_counts = {
                ProgressCode.Completed: 0,
                ProgressCode.Running: 0,
                ProgressCode.NotStarted: 0,
                ProgressCode.Errored: 0,
                ProgressCode.Failed: 0,
                ProgressCode.Paused: 0
            }

            total_children = self._count_descendants_unlocked(progress_id, status_counts)

            # Calculate completion percentage
            completion_percentage = 0.0
            if total_children > 0:
                completion_percentage = (status_counts[ProgressCode.Completed] / total_children) * 100.0

            # Determine aggregate status
            aggregate_status = self._determine_aggregate_status(status_counts, total_children)

            return {
                "progress_id": progress_id,
                "progress": progress.as_dict(),
                "total_children": total_children,
                "completed_count": status_counts[ProgressCode.Completed],
                "running_count": status_counts[ProgressCode.Running],
                "pending_count": status_counts[ProgressCode.NotStarted],
                "errored_count": status_counts[ProgressCode.Errored],
                "failed_count": status_counts[ProgressCode.Failed],
                "paused_count": status_counts[ProgressCode.Paused],
                "completion_percentage": completion_percentage,
                "aggregate_status": aggregate_status.name
            }

        finally:
            self._lock.release()

    def _count_descendants_unlocked(self, progress_id: str, status_counts: Dict[ProgressCode, int]) -> int:
        """
            Internal method to count descendants and collect status counts.
            Must be called with lock held.

            :param progress_id: The ID of the progress indicator.
            :param status_counts: Dictionary to accumulate status counts.

            :returns: Total number of descendants.

            :rtype: int
        """
        total = 0
        child_ids = self._parent_children_map.get(progress_id, [])

        for child_id in child_ids:
            if child_id in self._progress_tree:
                child = self._progress_tree[child_id]
                total += 1
                
                if child.status in status_counts:
                    status_counts[child.status] += 1

                # Recursively count descendants
                total += self._count_descendants_unlocked(child_id, status_counts)

        return total

    def _determine_aggregate_status(self, status_counts: Dict[ProgressCode, int],
                                    total_children: int) -> ProgressCode:
        """
            Determines the aggregate status based on child status counts.

            Status determination priority:
            1. If any child has Errored status -> Errored
            2. If any child has Failed status -> Failed
            3. If any child has Running status -> Running
            4. If any child has Paused status -> Paused
            5. If all children are Completed -> Completed
            6. If any child has NotStarted status -> NotStarted
            7. Default -> Running

            :param status_counts: Dictionary of status counts.
            :param total_children: Total number of children.

            :returns: The aggregate ProgressCode.

            :rtype: ProgressCode
        """
        if total_children == 0:
            return ProgressCode.NotStarted

        if status_counts[ProgressCode.Errored] > 0:
            return ProgressCode.Errored

        if status_counts[ProgressCode.Failed] > 0:
            return ProgressCode.Failed

        if status_counts[ProgressCode.Running] > 0:
            return ProgressCode.Running

        if status_counts[ProgressCode.Paused] > 0:
            return ProgressCode.Paused

        if status_counts[ProgressCode.Completed] == total_children:
            return ProgressCode.Completed

        if status_counts[ProgressCode.NotStarted] > 0:
            return ProgressCode.NotStarted

        return ProgressCode.Running

    def get_all_progress(self) -> Dict[str, dict]:
        """
            Retrieves all progress indicators as a dictionary.

            :returns: A dictionary mapping progress IDs to their dictionary
                      representations.

            :rtype: Dict[str, dict]
        """
        self._lock.acquire()
        try:
            result = {}
            for progress_id, progress in self._progress_tree.items():
                result[progress_id] = progress.as_dict()
            return result
        finally:
            self._lock.release()

    def get_progress_tree(self) -> dict:
        """
            Retrieves the complete progress tree as a nested dictionary structure.

            The returned structure contains root-level progress indicators with
            their children nested recursively.

            :returns: A dictionary containing the hierarchical progress tree.

            :rtype: dict
        """
        self._lock.acquire()
        try:
            roots = []
            for progress in self._progress_tree.values():
                if progress.parent_id is None:
                    roots.append(self._build_tree_node_unlocked(progress.id))
            
            return {
                "roots": roots,
                "total_count": len(self._progress_tree)
            }
        finally:
            self._lock.release()

    def _build_tree_node_unlocked(self, progress_id: str) -> dict:
        """
            Internal method to build a tree node with nested children.
            Must be called with lock held.

            :param progress_id: The ID of the progress indicator.

            :returns: A dictionary representing the tree node with children.

            :rtype: dict
        """
        if progress_id not in self._progress_tree:
            return {}

        progress = self._progress_tree[progress_id]
        node = progress.as_dict()

        # Build children recursively
        children = []
        child_ids = self._parent_children_map.get(progress_id, [])
        for child_id in child_ids:
            children.append(self._build_tree_node_unlocked(child_id))

        node["children"] = children

        return node

    def clear(self) -> None:
        """
            Clears all progress indicators from the aggregator.

            :returns: None
        """
        self._lock.acquire()
        try:
            self._progress_tree.clear()
            self._parent_children_map.clear()
        finally:
            self._lock.release()

    def __len__(self) -> int:
        """
            Returns the number of progress indicators in the aggregator.

            :returns: The count of progress indicators.

            :rtype: int
        """
        self._lock.acquire()
        try:
            return len(self._progress_tree)
        finally:
            self._lock.release()
