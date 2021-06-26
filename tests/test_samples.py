"""
Automate testing of samples
so that they do not throw any errors.
This is not a silver bullet: developers have
to double check the uploaded samples to ensure that
they function
"""
import os
import glob


def test_samples():
    try:
        for file in glob.iglob("../samples/*.py"):
            os.system("python3 " + file)
    except Exception as exc:
        assert False, f"'test_samples()' raised an exception {exc}"
