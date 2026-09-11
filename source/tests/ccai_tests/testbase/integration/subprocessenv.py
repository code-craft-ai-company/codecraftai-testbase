"""
    Shared helper for the integration tests that launch the testbase CLI in a
    subprocess with a deliberately minimal environment.
"""

import os
import platform


def minimal_subprocess_environment() -> dict:
    """
        Return a minimal environment for a child python process.

        Only PATH, HOME, USER, LANG and TERM are carried over from the parent, so a
        test cannot depend on the developer's shell by accident. On Windows the
        variables the operating system itself needs are kept as well: without
        SYSTEMROOT the WinSock provider cannot load and ``import asyncio`` fails
        with WinError 10106.
    """
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "TERM": os.environ.get("TERM", "xterm"),
    }

    if platform.system() == "Windows":
        for name in ("SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
                     "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PROGRAMDATA"):
            if name in os.environ:
                env[name] = os.environ[name]

    return env
