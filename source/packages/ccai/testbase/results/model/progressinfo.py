"""
    .. module:: ccai.testbase.results.model.progressinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for progressinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Optional


from dataclasses import dataclass
from datetime import datetime


from ccai.testbase.results.model.progresscode import ProgressCode
from ccai.testbase.results.model.progresstype import ProgressType


@dataclass
class ProgressInfo:
    """
        Representation of a single progress update event.
    """

    id: str
    category: str
    moniker: str
    ptype: ProgressType
    range_min: str
    range_max: str
    position: str
    status: ProgressCode
    when: datetime
    data: Optional[dict] = None

    def as_dict(self) -> dict:

        rtnval = {
            "id": self.id,
            "category": self.category,
            "moniker": self.moniker,
            "ptype": self.ptype.name,
            "range_min": self.range_min,
            "range_max": self.range_max,
            "position": self.position,
            "status": self.status.name,
            "when": self.when.isoformat()
        }

        if self.data is not None:
            rtnval["data"] = self.data
        else:
            rtnval["data"] = {}

        return rtnval
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProgressInfo":
        when = datetime.fromisoformat(data["when"])
        
        # Convert string values to enum types
        ptype = data["ptype"]
        if isinstance(ptype, str):
            ptype = ProgressType(ptype)
        
        status = data["status"]
        if isinstance(status, str):
            status = ProgressCode(status)

        inst = cls(data["id"], data["category"], data["moniker"], ptype, data["range_min"],
                   data["range_max"], data["position"], status, when, data.get("data"))
        return inst
    
    def __repr__(self):
        reprval = repr(self.as_dict())
        return reprval