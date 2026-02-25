"""
    .. module:: automojo.testbase.results.model.pipelineinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for pipelineinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass


@dataclass
class PipelineInfo:
    """
        Metadata describing the pipeline associated with a run.

        All fields are required and must be non-empty strings. Validation is
        performed automatically after initialization.

        :raises ValueError: If any required field is None or an empty string.
    """

    id: str # identifier such as a uuid which identifies a particular venue associated with the pipeline.
    name: str # name for the venue associated pipeline.
    instance: str # identifier such as a uuid which identifies an instance of a pipeline.

    def __post_init__(self):
        """
            Validates that all required fields are present and non-empty.

            This method is called automatically by the dataclass after __init__.
            It ensures that all PipelineInfo fields contain valid, non-empty string values.

            :raises ValueError: If any required field is None or an empty string.
                                The error message includes the name of the invalid field.
        """
        required_fields = ['id', 'name', 'instance']
        
        for field_name in required_fields:
            value = getattr(self, field_name)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                raise ValueError(
                    f"PipelineInfo field '{field_name}' is required and cannot be None or empty."
                )