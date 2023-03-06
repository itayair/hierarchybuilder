import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hierarchybuilder",
    version="0.0.1",
    author="Itay Yair",
    author_email="iy24592@gmail.com",
    description="implementation of hierarchy builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/itayair//hierarchybuilder",
    project_urls={
        "Bug Tracker": "https://github.com/itayair/hierarchybuilder/-/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6"
)
