import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hierarchybuilder",
    version="0.0.4",
    author="Itay Yair and Hillel Taub-Tabib and Yoav Goldberg",
    author_email="iy24592@gmail.com",
    description="implementation of hierarchy builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/itayair//hierarchybuilder",
    install_requires=[
        'fastapi==0.94.1',
        'nltk==3.8.1',
        'pandas==1.5.3',
        'quantulum3==0.8.1',
        'requests==2.28.2',
        'scikit_learn==1.2.0',
        'setuptools==60.2.0',
        'spacy==3.0.9',
        'torch==1.13.1',
        'tqdm==4.64.1',
        'transformers==4.26.1',
        'uvicorn==0.21.0'
    ],
    project_urls={
        "Bug Tracker": "https://github.com/itayair/hierarchybuilder/-/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7"
)
