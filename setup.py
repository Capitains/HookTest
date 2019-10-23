from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Pull requirements from requirements.txt file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    install_requires, tests_require = [], []
    now_we_have_dev = False
    for line in f:
        if line.startswith("#"):
             if "test" in line:
                   now_we_have_dev = True
        elif now_we_have_dev:
            tests_require.append(line.strip())
        else:
            install_requires.append(line.strip())

setup(
    name='HookTest',
    version="1.2.3",
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
    install_requires=install_requires,
    tests_require=tests_require,
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
