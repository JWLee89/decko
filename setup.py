import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="yeezy-pkg-YOUR-USERNAME-HERE", # Replace with your own username
    version="0.0.1",
    author="Jay Lee",
    author_email="ljay189@gmail.com",
    description="A simple utility belt for Python developers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JWLee89/yeezy",
    project_urls={
        "Bug Tracker": "https://github.com/JWLee89/yeezy/issues",
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