import setuptools
from src.decko import __version__, PROJECT_NAME

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=PROJECT_NAME,  # Replace with your own username
    version=__version__,
    author="Jay Lee",
    author_email="ljay189@gmail.com",
    description="A simple decorator based utility for helping with debugging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JWLee89/decko",
    project_urls={
        "Bug Tracker": "https://github.com/JWLee89/decko/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
