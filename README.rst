.. image:: https://coveralls.io/repos/Capitains/HookTest/badge.svg?service=github
  :alt: Coverage Status
  :target: https://coveralls.io/github/Capitains/HookTest
.. image:: https://travis-ci.org/Capitains/HookTest.svg
  :alt: Build Status
  :target: https://travis-ci.org/Capitains/HookTest
.. image:: https://badge.fury.io/py/HookTest.svg
  :alt: PyPI version
  :target: http://badge.fury.io/py/HookTest
.. image:: https://readthedocs.org/projects/docs/badge/?version=latest
    :alt: Documentation
    :target: https://capitains-hooktest.readthedocs.io/en/latest/
What ?
######

Capitains HookTest is a python library and commandline tool for testing Capitains CTS packages or CTS files individually.

Install
*******
To install it, simply do : :code:`pip3 install HookTest` or

.. code-block:: bash

    git clone https://github.com/Capitains/HookTest.git
    cd HookTest
    python3 setup.py install

From there, you will be able to call it in your python scripts with `ìmport HookTest` or you can use it in your terminal session

**Be careful, as Capitains requires java for Schematron and RelaxNG tests**

How ?
#####

The command is run with :code:`hooktest [-h] [-i UUID] [-r REPOSITORY] [-b BRANCH] [-w WORKERS] [-s SCHEME] [-v] [-j JSON] [-c] [-p PING] [-f FINDER] path` where Path is the path to the containing repository (in which there is a folder data/)

+----------------------------------------+----------------------------------------------------------------------+
| Parameter in console                   | Detail about the Parameter                                           |
+========================================+======================================================================+
| -h, --help                             | show this help message and exit                                      |
+----------------------------------------+----------------------------------------------------------------------+
| -i UUID, --uuid UUID                   | Identifier for a test. This will be used as a temporary folder name  |
+----------------------------------------+----------------------------------------------------------------------+
| -r REPOSITORY, --repository REPOSITORY | Name of the git repository                                           |
+----------------------------------------+----------------------------------------------------------------------+
| -b BRANCH, --branch BRANCH             | Reference for the branch                                             |
+----------------------------------------+----------------------------------------------------------------------+
| -w WORKERS, --workers WORKERS          | Number of workers to be used                                         |
+----------------------------------------+----------------------------------------------------------------------+
| -s SCHEME, --scheme SCHEME             | 'tei' or 'epidoc' scheme to be used                                  |
+----------------------------------------+----------------------------------------------------------------------+
| -v, --verbose                          | Show RNG's errors and other details                                  |
+----------------------------------------+----------------------------------------------------------------------+
| -j JSON, --json JSON                   | Save to specified json file the results                              |
+----------------------------------------+----------------------------------------------------------------------+
| -c, --console                          | Print to console                                                     |
+----------------------------------------+----------------------------------------------------------------------+
| -p PING, --ping PING                   | Send results to a server                                             |
+----------------------------------------+----------------------------------------------------------------------+
| -f FINDER, --finder Finder             | Filter using the last part of the URN (eg. tlg0001.tlg001, tlg0001,  |
|                                        | tlg0001.tlg001.p-grc1 for urn:cts:greekLit:tlg0001.tlg001.p-grc1     |
+----------------------------------------+----------------------------------------------------------------------+
| --countword                            | Count words in texts passing the tests                               |
+----------------------------------------+----------------------------------------------------------------------+

Licenses
########

TEI and EpiDoc Schema
*********************

The TEI Schema is copyright the TEI Consortium (http://www.tei-c.org/Guidelines/access.xml#body.1_div.2). To the extent that the EpiDoc ODD and schema have been customized and amount to transformative versions of the original schema, they are copyright Gabriel Bodard and the other contributors (as listed in tei:revisionDesc). See LICENSE.txt for license details.
