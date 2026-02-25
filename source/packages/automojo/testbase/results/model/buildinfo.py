"""
    .. module:: automojo.testbase.results.model.buildinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for buildinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from dataclasses import dataclass


@dataclass
class BuildInfo:
    """
        Information describing a build under test.

        All fields are required and must be non-empty strings. Validation is
        performed automatically after initialization.

        :raises ValueError: If any required field is None or an empty string.
    """

    branch: str # name of a code 'branch' to associate with the results.
    build: str # name of a product 'build' to associate with the results
    flavor: str # label that indicates the flavor of build the automation is running against.
    release: str # name of a release to associate a automation run with.
    url: str # build url

    def __post_init__(self):
        """
            Validates that all required fields are present and non-empty.

            This method is called automatically by the dataclass after __init__.
            It ensures that all BuildInfo fields contain valid, non-empty string values.

            :raises ValueError: If any required field is None or an empty string.
                                The error message includes the name of the invalid field.
        """
        required_fields = ['branch', 'build', 'flavor', 'release', 'url']
        
        for field_name in required_fields:
            value = getattr(self, field_name)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                raise ValueError(
                    f"BuildInfo field '{field_name}' is required and cannot be None or empty."
                )
