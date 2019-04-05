.. image:: docs/_static/images/header.png
   :scale: 80 %
   :align: center


----------


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
.. image:: https://zenodo.org/badge/40954877.svg
   :target: https://zenodo.org/badge/latestdoi/40954877
.. image:: https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg
   :alt: License: MPL 2.0
   :target: https://opensource.org/licenses/MPL-2.0
    

----------


* `What are HookTest and CapiTainS`_
* `How to use locally`_ 
* `Running HookTest on Travis CI`_ 
* `Licenses`_

What are HookTest and CapiTainS
###############################

+-----------+-----------------------------------------------------------------------------------------------------------------------------+
| |logoCap| | CapiTainS provides resources for people to publish, use and reuse texts with/for standards API.                             |
|           |                                                                                                                             |
|           | Capitains HookTest is a python library and commandline tool for testing Capitains textual repositories with their metadata. |
+-----------+-----------------------------------------------------------------------------------------------------------------------------+



.. |logoCap| image:: docs/_static/images/capitains.png
    :target: http://capitains.github.io

Installation Instructions
*************************
To install it, simply do : :code:`pip3 install HookTest` or

.. code-block:: bash

    git clone https://github.com/Capitains/HookTest.git
    cd HookTest
    python3 setup.py install

From there, you will be able to call it in your python scripts with `import HookTest` or you can use it in your terminal session

**Be careful, as Capitains requires java for Schematron and RelaxNG tests**

How to use locally
##################

The command is run with :code:`hooktest [-h] [-w WORKERS] [-s SCHEME] [-v] [-j JSON] [-c] [-p PING] [-f FINDER] path` where Path is the path to the containing repository (in which there is a folder data/)

+----------------------------------------+----------------------------------------------------------------------+
| Parameter in console                   | Detail about the Parameter                                           |
+========================================+======================================================================+
| -h, --help                             | show this help message and exit                                      |
+----------------------------------------+----------------------------------------------------------------------+
| -w WORKERS, --workers WORKERS          | Number of workers to be used                                         |
+----------------------------------------+----------------------------------------------------------------------+
| -s SCHEME, --scheme SCHEME             |Possible Values:                                                      |
|                                        |                                                                      |
|                                        |* "tei": Use the most recent TEI-ALL DTD                              |
|                                        |* "epidoc": Use the most recent epiDoc DTD                            |
|                                        |* "ignore": Perform no schema validation                              |
|                                        |* "auto" (Default) - Automatically detect the RNG to use from the     |
|                                        |  xml-model declaration in each individual XML file. If the reference |
|                                        |  is to a remote URL, the file will be downloaded and used.           |
|                                        |* <filepath>: If a file path is given, this should refer to a local   |
|                                        |  RNG file that should be used to check all text documents            |
|                                        |                                                                      |
+----------------------------------------+----------------------------------------------------------------------+
| --guidelines                           |Possible Values:                                                      |
|                                        |                                                                      |
|                                        |* "2.tei" (Default) - Will use version 2.0 of the CapiTainS guidelines|
|                                        |  for generic TEI texts.                                              |
|                                        |* "2.epidoc" - Will use version 2.0 of the CapiTainS guidelines for   |
|                                        |  EpiDoc encoded texts.                                               |
|                                        |                                                                      |
|                                        |(Details at http://capitains.org/pages/guidelines#urn-information)    |
+----------------------------------------+----------------------------------------------------------------------+
| -v, --verbose [{0,5,7,10}]             |Verbose Level                                                         |
|                                        |                                                                      |
|                                        |- 0 (Default) Only show necessary Information                         |
|                                        |- 5 Show duplicate or forbidden characters                            |
|                                        |- 7 All of before + show failing units                                |
|                                        |- 10 All available details                                            |
|                                        |                                                                      |
+----------------------------------------+----------------------------------------------------------------------+
| -j JSON, --json JSON                   | Save to specified json file the results                              |
+----------------------------------------+----------------------------------------------------------------------+
| -c, --console                          | Print to console                                                     |
+----------------------------------------+----------------------------------------------------------------------+
| -f FILTER, --filter FILTER             | Filter using the last part of the URN (eg. tlg0001.tlg001, tlg0001,  |
|                                        | tlg0001.tlg001.p-grc1 for urn:cts:greekLit:tlg0001.tlg001.p-grc1     |
+----------------------------------------+----------------------------------------------------------------------+
| --countword                            | Count words in texts passing the tests                               |
+----------------------------------------+----------------------------------------------------------------------+
| --manifest                             | Produce a Manifest                                                   |
+----------------------------------------+----------------------------------------------------------------------+
| --allowfailure                         | Returns a passing test result as long as at least one text passes    |
+----------------------------------------+----------------------------------------------------------------------+

Debugging
#########

Note that you can run some debugging function adding `HOOKTEST_DEBUG=True` before your command : `HOOKTEST_DEBUG=True hooktest --console --scheme tei --workers 1 --verbose 10  --countword --allowfailure ./ --scheme ignore`.
It will display more informations in case tests struggle to go from one file to another. We recommend using only one worker in this context.


Running HookTest on Travis CI
#############################

HookTest can now be run on the Travis Continuous Integration (CI) platform. This relieves the need for HookTest user to set up their own HookTest testing server and also allows for automatic building of corpus releases after successful tests. To set up your Github CapiTainS text repository to use Travis CI, the first step is to set up your account at Travis (https://docs.travis-ci.com/user/getting-started). Follow step 1 and step 2 on that web page to set up your repository on Travis.

Once you have done this, you will need to add a `.travis.yml` file to root folder of your repository. (Note that the name of the file starts with a period ('.').) Use the following as a template for your own `.travis.yml` file:

.. code-block:: yaml

    language: python
    python:
    - '3.5'
    install:
    - pip3 install HookTest
    script:  hooktest --console --scheme epidoc --workers 3 --verbose 5 --manifest --countword --allowfailure ./
    before_deploy:
    - hooktest-build --travis --txt ./
    - results=$(cat manifest.txt)
    - DATE=`date +%Y-%m-%d`
    - git config --global user.email "builds@travis-ci.com"
    - git config --global user.name "Travis CI"
    - export GIT_TAG=$major_version.$minor_version.$TRAVIS_BUILD_NUMBER
    - git add -A
    - git tag $GIT_TAG -a -m "$DATE" -m "PASSING FILES" -m "$results"
    - git push -q https://$GITPERM@github.com/YOUR_REPOSITORY_NAME --tags
    - ls -R

    deploy:
      provider: releases
      api_key: $GITPERM
      skip_cleanup: true
      on:
	repo: YOUR_REPOSITORY_NAME
	branch: master

    env:
      global:
	major_version: 0
	minor_version: 0
	
To help you set up this file for your own repository, a line-by-line explanation follows.

.. code-block:: yaml

    language: python
    python:
    - '3.5'
    install:
    - pip3 install HookTest>=1.0.0


These first 5 lines are for the basic setup of HookTest on Travis. Do not change them.

.. code-block:: yaml

    script: hooktest --scheme epidoc --workers 3 --verbose --manifest --console --countword --allowfailure ./


This line runs HookTest. The parameters are those described in the parameter table above. If you do not want to make a new release of your corpus unless it is 100% CapiTainS-compliant, then remove the `--allowfailure` parameter. Without this parameter, the build will fail if the corpus is not 100% compliant causing Travis to skip the build and release steps. Because of the way Travis is set up, we recommend not setting `--workers` higher than 3.

.. code-block:: yaml

    before_deploy:
    - hooktest-build --travis --txt ./
    - results=$(cat manifest.txt)
    - DATE=`date +%Y-%m-%d`
    - git config --global user.email "builds@travis-ci.com"
    - git config --global user.name "Travis CI"
    - export GIT_TAG=$major_version.$minor_version.$TRAVIS_BUILD_NUMBER
    - git add -A
    - git tag $GIT_TAG -a -m "$DATE" -m "PASSING FILES" -m "$results"
    - git push -q https://$GITPERM@github.com/YOUR_REPOSITORY_NAME --tags
    - ls -R

Once HookTest has run on Travis, if the repository is 100% CapiTainS-compliant or if the `--allowfailure` parameter was set and at least one text, along with all of its metadata files, passed, then Travis carries out the build step. Of special note here is the `hooktest-build --travis --txt ./` line. The `hooktest-build` class is designed to build the passing files in a repository into a release. To this point, it has been implemented only for Travis CI. This script basically removes all failing files from the repository. The `--txt` parameter then converts each of the passing XML text files to plain text, with each citation unit separated by two carriage returns, e.g.,::

    Lorem ipsum dolor sit amet, consectetur adipiscing elit...
    
    Lorem ipsum dolor sit amet, consectetur adipiscing elit...
    
Simply remove the --txt parameter from the `.travis.yml` file if you would prefer not to release plain text versions of your texts.

Of special note here are two things that you will need to set up yourself. The first is the environment variable `$GITPERM`. This variable should contain the value of a Github OAuth token that you have set up for your Github account. To find out how to set up such a token, see the Github documentation at https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/. Your OAuth token should have the `repo` scope (https://developer.github.com/v3/oauth/#scopes). Once you have created this token, you should define this as the `GITPERM` environment variable for this repository in Travis. To do this, see the documentation here: https://docs.travis-ci.com/user/environment-variables/#Defining-Variables-in-Repository-Settings. Make sure that the switch for "Display value in build log" is set to off, otherwise anyone looking at your build log will be able to see your private OAuth token.

The second important change to this line is to replace the string "YOUR_REPOSITORY_NAME" with the Github user name or organization name and the repository name, e.g., "OpenGreekAndLatin/First1KGreek". If any of these pre-deployment steps fail, then the repository will not build and release.

.. code-block:: yaml

    deploy:
      provider: releases
      api_key: $GITPERM
      skip_cleanup: true
      on:
	repo: YOUR_REPOSITORY_NAME
	branch: master
	
    env:
      global:
	major_version: 0
	minor_version: 0

These lines define the deployment and release of your repository to Github. They will create a release on Github that has as its lable the major_version.minor_version.$TRAVIS_BUILD_NUMBER. You should set the major_version and minor_version environment variables to match the release status of your repository. 

Once you have created and tailored this `.travis.yml` file to your repository, you should then push it to your Github corpus repository. If you have set up Travis to test with repository, as described above, then Travis should read this `.travis.yml` file and automatically run HookTest and, if appropriate, build your first automatic release for the repository.

Licenses
########

TEI and EpiDoc Schema
*********************

The TEI Schema is copyright the TEI Consortium (http://www.tei-c.org/Guidelines/access.xml#body.1_div.2). To the extent that the EpiDoc ODD and schema have been customized and amount to transformative versions of the original schema, they are copyright Gabriel Bodard and the other contributors (as listed in tei:revisionDesc). See LICENSE.txt for license details.
