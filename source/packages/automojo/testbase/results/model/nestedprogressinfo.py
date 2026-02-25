"""
    .. module:: automojo.testbase.results.model.nestedprogressinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for nested progress information supporting hierarchical progress tracking.

    .. moduleauthor:: AutomationX
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List, Optional

from dataclasses import dataclass, field
from datetime import datetime

from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progresstype import ProgressType
from automojo.testbase.results.model.progressinfo import ProgressInfo


@dataclass
class NestedProgressInfo(ProgressInfo):
    """
        Representation of a nested progress update event that supports hierarchical
        progress tracking.

        This class extends :class:`ProgressInfo` to add support for parent-child
        relationships between progress indicators. This enables tracking of complex
        multi-level progress scenarios such as:

        - A test suite containing multiple test modules
        - A test module containing multiple test functions
        - A distributed task containing multiple sub-tasks

        The parent_id field links child progress indicators to their parent,
        allowing the progress tracking system to build and maintain a tree
        structure of progress information.

        Attributes:
            parent_id: Optional identifier of the parent progress indicator.
                       If None, this is a root-level progress indicator.
            children_ids: List of child progress indicator IDs. This is populated
                          by the progress aggregator when building the tree.
            depth: The depth level in the progress hierarchy (0 for root).

        Example Usage::

            # Create a parent progress indicator for a test suite
            suite_progress = NestedProgressInfo(
                id="suite-123",
                category="test-suite",
                moniker="Integration Tests",
                ptype=ProgressType.NumericRange,
                range_min="0",
                range_max="100",
                position="0",
                status=ProgressCode.Running,
                when=datetime.now(),
                parent_id=None,  # Root level
                depth=0
            )

            # Create a child progress indicator for a test module
            module_progress = NestedProgressInfo(
                id="module-456",
                category="test-module",
                moniker="test_authentication",
                ptype=ProgressType.Sequential,
                range_min="0",
                range_max="10",
                position="3",
                status=ProgressCode.Running,
                when=datetime.now(),
                parent_id="suite-123",  # Links to parent
                depth=1
            )
    """

    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    depth: int = 0

    def as_dict(self) -> dict:
        """
            Converts the nested progress info to a dictionary representation.

            This method extends the base :class:`ProgressInfo.as_dict` method to
            include the additional nested progress fields (parent_id, children_ids,
            depth).

            :returns: A dictionary containing all progress fields including
                      nested hierarchy information.

            :rtype: dict
        """
        rtnval = super().as_dict()

        rtnval["parent_id"] = self.parent_id
        rtnval["children_ids"] = list(self.children_ids)
        rtnval["depth"] = self.depth

        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "NestedProgressInfo":
        """
            Creates a NestedProgressInfo instance from a dictionary.

            This class method deserializes a dictionary representation back into
            a NestedProgressInfo object, handling type conversions for enum fields
            and datetime parsing.

            :param data: A dictionary containing the serialized progress data.

            :returns: A new NestedProgressInfo instance populated with the
                      dictionary data.

            :rtype: NestedProgressInfo
        """
        when = datetime.fromisoformat(data["when"])

        # Convert string values to enum types
        ptype = data["ptype"]
        if isinstance(ptype, str):
            ptype = ProgressType(ptype)

        status = data["status"]
        if isinstance(status, str):
            status = ProgressCode(status)

        inst = cls(
            id=data["id"],
            category=data["category"],
            moniker=data["moniker"],
            ptype=ptype,
            range_min=data["range_min"],
            range_max=data["range_max"],
            position=data["position"],
            status=status,
            when=when,
            data=data.get("data"),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            depth=data.get("depth", 0)
        )

        return inst

    @classmethod
    def from_progress_info(cls, progress: ProgressInfo, parent_id: Optional[str] = None,
                           depth: int = 0) -> "NestedProgressInfo":
        """
            Creates a NestedProgressInfo from an existing ProgressInfo instance.

            This factory method allows converting a flat ProgressInfo into a
            nested progress indicator by adding parent relationship and depth
            information.

            :param progress: The source ProgressInfo to convert.
            :param parent_id: Optional parent progress indicator ID.
            :param depth: The depth level in the hierarchy.

            :returns: A new NestedProgressInfo instance with the same data as
                      the source plus nested hierarchy fields.

            :rtype: NestedProgressInfo
        """
        return cls(
            id=progress.id,
            category=progress.category,
            moniker=progress.moniker,
            ptype=progress.ptype,
            range_min=progress.range_min,
            range_max=progress.range_max,
            position=progress.position,
            status=progress.status,
            when=progress.when,
            data=progress.data,
            parent_id=parent_id,
            children_ids=[],
            depth=depth
        )

    def add_child(self, child_id: str) -> None:
        """
            Adds a child progress indicator ID to this progress indicator.

            :param child_id: The ID of the child progress indicator to add.

            :returns: None
        """
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)

    def remove_child(self, child_id: str) -> None:
        """
            Removes a child progress indicator ID from this progress indicator.

            :param child_id: The ID of the child progress indicator to remove.

            :returns: None
        """
        if child_id in self.children_ids:
            self.children_ids.remove(child_id)

    def __repr__(self):
        reprval = repr(self.as_dict())
        return reprval
