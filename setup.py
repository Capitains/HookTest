from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='HookTest',
    version="1.2.0",
    description='Hook Test Script for GitHub/CapiTainS repositories',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url='http://github.com/Capitains/HookTest',
    author='Thibault Clérice, Matt Munson',
    author_email='leponteineptique@gmail.com',
    license='Mozilla Public License Version 2.0',
    packages=find_packages(exclude=("tests")),
    classifiers=[
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Version Control",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Text Processing :: General",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"
    ],
    install_requires=[
        "MyCapytain>=2.0.0",
        "jingtrang==0.1.1",
        "GitPython==2.1.0",
        "requests>=2.8.1",
        "prettytable==0.7.2",
        "ansicolors==1.0.2"
    ],
    tests_require=[
        "mock==1.3.0",
        "six>=1.10.0",
    ],
    package_data={
        'HookTest': ['resources/*.rng']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'hooktest=HookTest.cmd:cmd',
            'hooktest-build=HookTest.cmd:cmd_build'
        ]
    },
    test_suite="tests",
    zip_safe=False
)
