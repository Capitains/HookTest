from setuptools import setup, find_packages


setup(
    name='HookTest',
    version="0.0.1",
    description='Hook Test Script for GitHub/CTS repositories',
    url='http://github.com/Capitains/HookTest',
    author='Thibault Clérice',
    author_email='leponteineptique@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        "MyCapytain==0.0.3",
        "jingtrang==0.1.1",
        "GitPython==1.0.1"
    ],
    package_data={
        'HookTest': ['resources/*.rng']
    },
    tests_require=[
    ],
    test_suite="tests",
    zip_safe=False
)
