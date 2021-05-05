from typing import Dict


class NotClassException(TypeError):
    """
    Occurs when Object is Not a Class
    """
    def __init__(self, msg):
        super().__init__(msg)


class NotClassOrCallableError(TypeError):
    """
    Called when users perform the following action:
    User attaches decorator to objects that are not
       - Classses
       - callable (functions)
    """

    def __init__(self, message: str, errors: Dict = None) -> None:
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.errors = errors


class FunctionAlreadyAddedError(ValueError):
    def __init__(self, message: str, errors: Dict = None) -> None:
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.errors = errors