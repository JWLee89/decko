from typing import Dict


class NotClassOrCallableError(TypeError):
    """
    Called when users perform the following action:

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
