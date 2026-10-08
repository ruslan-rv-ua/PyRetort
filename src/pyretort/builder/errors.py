from __future__ import annotations


class BuildError(Exception):
    """A build failure that is expected and explained in the message.

    The message is meant for the user: the CLI prints it as is, without a
    traceback, and exits with code 1.
    """
