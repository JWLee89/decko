from typing import Dict


class NotClassOrCallable(TypeError):
    """
    Called when users perform the following action:

    """

    def __init__(self, message: str, errors: Dict = None) -> None:
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.errors = errors
