Capitains HookTest
===

[![Coverage Status](https://coveralls.io/repos/Capitains/HookTest/badge.svg?service=github)](https://coveralls.io/github/Capitains/HookTest)
[![Build Status](https://travis-ci.org/Capitains/HookTest.svg)](https://travis-ci.org/Capitains/HookTest)
[![PyPI version](https://badge.fury.io/py/HookTest.svg)](http://badge.fury.io/py/HookTest)

## What ?

Capitains HookTest is a python library and commandline tool for testing Capitains CTS packages or CTS files individually. To install it, simply do : `pip3 install HookTest` (*Not available yet*) or `python3 setup.py install`. From there, you will be able to call it in your python scripts with `ìmport HookTest` or you can use it in your terminal session :

```
usage: HookTest-Local [-h] [-i UUID] [-r REPOSITORY] [-b BRANCH] [-w WORKERS]
                      [-s SCHEME] [-v] [-p PING]
                      path

HookTest provides local and easy to use tests for CTS resources package

positional arguments:
  path                  Path containing the repository

optional arguments:
  -h, --help            show this help message and exit
  -i UUID, --uuid UUID  Identifier for a test. This will be used as a
                        temporary folder name
  -r REPOSITORY, --repository REPOSITORY
                        Name of the git repository
  -b BRANCH, --branch BRANCH
                        Reference for the branch
  -w WORKERS, --workers WORKERS
                        Number of workers to be used
  -s SCHEME, --scheme SCHEME
                        'tei' or 'epidoc' scheme to be used
  -v, --verbose         Show RNG's errors
  -p PING, --ping PING  Send results to a server
```

## Licenses

### TEI and EpiDoc Schema

The TEI Schema is copyright the TEI Consortium (http://www.tei-c.org/Guidelines/access.xml#body.1_div.2). To the extent that the EpiDoc ODD and schema have been customized and amount to transformative versions of the original schema, they are copyright Gabriel Bodard and the other contributors (as listed in tei:revisionDesc). See LICENSE.txt for license details.