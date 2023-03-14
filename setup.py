import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hierarchybuilder",
    version="0.0.32",
    author="Itay Yair",
    author_email="iy24592@gmail.com",
    description="implementation of hierarchy builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/itayair//hierarchybuilder",
    # install_requires=[
    #     'quantulum3==0.8.1',
    #     'scipy==1.10.1',
    #     'torch==1.13.1',
    #     'spacy-legacy==3.0.12',
    #     'spacy==3.0.9',
    #     'spacy-loggers==1.0.4',
    #     'transformers==4.26.1',
    #     'uvicorn==0.20.0',
    #     'fastapi==0.92.0',
    #     'huggingface-hub==0.12.1',
    #     'numpy==1.24.2',
    #     'scikit-learn==1.2.0',
    #     'sklearn==0.0.post1'
    # ],
    install_requires=[
        'fastapi>=0.90.0',
        'nltk>=3.8.1',
        'pandas>=1.5.0',
        'quantulum3>=0.8.1',
        'requests>=2.28.2',
        'scikit_learn>=1.2.0',
        'setuptools>=60.2.0',
        'spacy>=3.0.6',
        'torch>=1.10.1',
        'tqdm>=4.64.0',
        'transformers>=4.11.3',
        'uvicorn>=0.20.0'
    ],
    dependency_links=['en-ud-model-sm @ https://storage.googleapis.com/en_ud_model/en_ud_model_sm-2.0.0.tar.gz'],
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
