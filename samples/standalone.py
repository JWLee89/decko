"""
Demo code for standalone decorators.
Will be added in version 0.3
"""

from src.decko.decorators import raise_error_if

if __name__ == "__main__":

    @raise_error_if(lambda x: True)
    def run(a):
        return a

    run(10)