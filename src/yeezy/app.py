import sys
import os
from typing import Callable


class Yeezy:
    """
    Yeeeee ....
    Entry point of the application.
    Architected as follows:

    -
    """
    def __init__(self,
                 root_path: str = None):

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = root_path

        # Dictionary mapping function names to debug functions
        # E.g. "do_work" -- <Callable>
        self.debug_functions = {}

        # Dictionary of custom decorators added by users
        # Warning: do not modify this dictionary as it may cause unexpected behaviors
        self.custom_decorators = {}

    def debug(self) -> Callable:
        """
        Used for running the trace function
        Example:
            yeezy.debug()
            def test():
                print("hello world")
        :rtype:
        """

    def register(self, decorator_name, *args, **kwargs):
        if decorator_name in self.custom_decorators:
           print(f"Warning: decorator name already exist ... Overwriting ...")

    def __repr__(self) -> str:
        return "Yee ... yeezy :)"

    def profile(self) -> None:
        """
        Profile all the registered stuff
        :return:
        :rtype:
        """
