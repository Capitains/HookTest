from setuptools import setup, find_packages


setup(
    name='HookTest',
    version="0.1.1",
    description='Hook Test Script for GitHub/CTS repositories',
    url='http://github.com/Capitains/HookTest',
    author='Thibault Clérice',
    author_email='leponteineptique@gmail.com',
    license='MIT',
    packages=find_packages(exclude=("tests")),
    install_requires=[
        "MyCapytain==1.0.4",
        "jingtrang==0.1.1",
        "GitPython==1.0.1",
        "requests>=2.7.0"
    ],
    tests_require=[
        "mock==1.3.0",
        "six>=1.9.0",
    ],
    package_data={
        'HookTest': ['resources/*.rng']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['hooktest=HookTest.cmd:cmd'],
    },
    test_suite="tests",
    zip_safe=False
)
