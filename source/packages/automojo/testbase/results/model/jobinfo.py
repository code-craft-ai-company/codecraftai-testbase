"""
    .. module:: automojo.testbase.results.model.jobinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for jobinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

import warnings

from dataclasses import dataclass


class MissingOptionalFieldWarning(UserWarning):
    """
        Warning issued when an optional field in JobInfo is not provided.

        This warning helps developers identify when optional metadata fields
        are missing, which may affect result reporting or correlation with
        external systems.

        The warning can be filtered using Python's standard warning filtering
        mechanisms if desired.
    """
    pass


@dataclass
class JobInfo:
    """
        Descriptor for job execution metadata.

        Required fields (id, name, type) must be non-empty strings. Optional fields
        (owner, label, initiator, venue, seed, tag) will generate warnings if not
        provided, to help identify potentially missing metadata.

        :raises ValueError: If any required field (id, name, type) is None or empty.
    """

    id: str # identifier for a job from the runner perspective
    name: str # name of the job.
    type: str # job type.
    owner: Optional[str] = None # Optional owner of the job.
    label: Optional[str] = None # Optional label associated with the job.
    initiator: Optional[str] = None # Optional name of the initiator of the job.
    venue: Optional[str] = None # Optional identifier of a venue the job was run in.
    seed: Optional[str] = None # Optional seed for the job.
    tag: Optional[str] = None # Optional correlation tag to associate with the job.

    def __post_init__(self):
        """
            Validates required fields and warns about missing optional fields.

            This method is called automatically by the dataclass after __init__.
            It ensures that required fields contain valid, non-empty string values
            and issues warnings for any optional fields that are not provided.

            :raises ValueError: If any required field (id, name, type) is None or empty.
                                The error message includes the name of the invalid field.
        """
        # Validate required fields
        required_fields = ['id', 'name', 'type']
        
        for field_name in required_fields:
            value = getattr(self, field_name)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                raise ValueError(
                    f"JobInfo field '{field_name}' is required and cannot be None or empty."
                )
        
        # Warn about missing optional fields
        optional_fields = ['owner', 'label', 'initiator', 'venue', 'seed', 'tag']
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is None:
                warnings.warn(
                    f"JobInfo optional field '{field_name}' is not set. "
                    f"Consider providing this field for better result correlation.",
                    MissingOptionalFieldWarning,
                    stacklevel=2
                )