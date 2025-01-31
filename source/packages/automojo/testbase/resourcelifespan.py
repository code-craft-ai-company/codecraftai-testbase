__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import enum

class ResourceLifespan(str, enum.Enum):
    Session = "session"
    Package = "package"
    Test = "test"
    Task = "task"
