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
| --travis                               | Produce Travis output                                                |
+----------------------------------------+----------------------------------------------------------------------+
| -p PING, --ping PING                   | Send results to a server                                             |
+----------------------------------------+----------------------------------------------------------------------+
| -f FINDER, --finder Finder             | Filter using the last part of the URN (eg. tlg0001.tlg001, tlg0001,  |
|                                        | tlg0001.tlg001.p-grc1 for urn:cts:greekLit:tlg0001.tlg001.p-grc1     |
+----------------------------------------+----------------------------------------------------------------------+
| --countword                            | Count words in texts passing the tests                               |
+----------------------------------------+----------------------------------------------------------------------+
| --travis                               | Produce Travis-friendly console output                               |
+----------------------------------------+----------------------------------------------------------------------+
| --allowfailure                         | Returns a passing test result as long as at least one text passes    |
+----------------------------------------+----------------------------------------------------------------------+

Running HookTest on Travis CI
#############################

HookTest can now be run on the Travis Continuous Integration (CI) platform. This relieves the need for HookTest user to set up their own HookTest testing server and also allows for automatic building of corpus releases after successful tests. To set up your Github CapiTainS text repository to use Travis CI, the first step is to set up your account at Travis (https://docs.travis-ci.com/user/getting-started). Follow step 1 and step 2 on that web page to set up your repository on Travis.

Once you have done this, you will need to add a `.travis.yml` file to root folder of your repository. (Note that the name of the file starts with a period ('.').) Use the following as a template for your own `.travis.yml` file:

.. code-block:: yml

    language: python
    python:
    - '3.5'
    install:
    - pip3 install HookTest
    script: hooktest --scheme epidoc --workers 3 --verbose --travis --countword --allowfailure ./
    before_deploy:
    - hooktest-build --travis ./
    - results=$(cat manifest.txt)
    - DATE=`date +%Y-%m-%d`
    - git config --global user.email "builds@travis-ci.com"
    - git config --global user.name "Travis CI"
    - export GIT_TAG=$major_version.$minor_version.$TRAVIS_BUILD_NUMBER
    - git tag $GIT_TAG -a -m "$DATE" -m "PASSING FILES" -m "$results"
    - git push -q https://$GITPERM@github.com/YOUR_REPOSITORY_NAME --tags
    - ls -R

    deploy:
      provider: releases
      api_key:
	secure: YOUR_SECURE_GITHUB_OATH_TOKEN
      file: release.tar.gz
      skip_cleanup: true
      on:
	repo: YOUR_REPOSITORY_NAME
	branch: master

    env:
      global:
	major_version: 0
	minor_version: 0
	
To help you set up this file for your own repository, a line-by-line explanation follows.

.. code-block:: yml

    language: python
    python:
    - '3.5'
    install:
    - pip3 install HookTest


These first 5 lines are for the basic setup of HookTest on Travis. Do not change them.

.. code-block:: yml

    script: hooktest --scheme epidoc --workers 3 --verbose --travis --countword --allowfailure ./


This line runs HookTest. The parameters are those described in the parameter table above. If you do not want to make a new release of your corpus unless it is 100% CapiTainS-compliant, then remove the `--allowfailure` parameter. Without this parameter, the build will fail if the corpus is not 100% compliant causing Travis to skip the build and release steps. Because of the way Travis is set up, we recommend not setting `--workers` higher than 3.

.. code-block:: yml

    before_deploy:
    - hooktest-build --travis ./
    - results=$(cat manifest.txt)
    - DATE=`date +%Y-%m-%d`
    - git config --global user.email "builds@travis-ci.com"
    - git config --global user.name "Travis CI"
    - export GIT_TAG=$major_version.$minor_version.$TRAVIS_BUILD_NUMBER
    - git tag $GIT_TAG -a -m "$DATE" -m "PASSING FILES" -m "$results"
    - git push -q https://$GITPERM@github.com/YOUR_REPOSITORY_NAME --tags
    - ls -R

Once HookTest has run on Travis, if the repository is 100% CapiTainS-compliant or if the `--allowfailure` parameter was set and at least one text, along with all of its metadata files, passed, then Travis carries out the build step. Of special note here are two things that you will need to set up yourself. The first is the environment variable `$GITPERM`. This variable should contain the value of a Github OAuth token that you have set up for your Github account. To find out how to set up such a token, see the Github documentation at https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/. Your OAuth token should have the `repo` scope (https://developer.github.com/v3/oauth/#scopes). Once you have created this token, you should define this as the `GITPERM` environment variable for this repository in Travis. To do this, see the documentation here: https://docs.travis-ci.com/user/environment-variables/#Defining-Variables-in-Repository-Settings. Make sure that the switch for "Display value in build log" is set to off, otherwise anyone looking at your build log will be able to see your private OAuth token.

The second important change to this line is to replace the string "YOUR_REPOSITORY_NAME" with the Github user name or organization name and the repository name, e.g., "OpenGreekAndLatin/First1KGreek". If any of these pre-deployment steps fail, then the repository will not build and release.

.. code-block:: yml

    deploy:
      provider: releases
      api_key:
	secure: YOUR_SECURE_GITHUB_OATH_TOKEN
      file: release.tar.gz
      skip_cleanup: true
      on:
	repo: YOUR_REPOSITORY_NAME
	branch: master
	
    env:
      global:
	major_version: 0
	minor_version: 0

These lines define the deployment and release of your repository to Github. They will zip all of the passing files into the `release.tar.gz` file and then create a release on Github that has as its lable the major_version.minor_version.$TRAVIS_BUILD_NUMBER. You should set the major_version and minor_version environment variables to match the release status of your repository. Besides the major_version and minor_version environment variables, there are two other changes that you should make to these lines for each individual repository. The first is to replace the string "YOUR_SECURE_GITHUB_OATH_TOKEN" with an encrypted Github OAuth token that is produced by Travis for precisely this purpose. See the documentation at https://docs.travis-ci.com/user/deployment/releases/#Authenticating-with-an-Oauth-token to find out how to produce such an encrypted OAuth token. We suggest that you first remove the `deploy` section from your `.travis.yml` file, then use the `travis setup releases` command to produce a `deploy` section that is tailored to your repository, and then add the missing lines from the `deploy` code block above to finish the file off.

Once you have created and tailored this `.travis.yml` file to your repository, you should then push it to your Github corpus repository. If you have set up Travis to test with repository, as described above, then Travis should read this `.travis.yml` file and automatically run HookTest and, if appropriate, build your first automatic release for the repository.

Licenses
########

TEI and EpiDoc Schema
*********************

The TEI Schema is copyright the TEI Consortium (http://www.tei-c.org/Guidelines/access.xml#body.1_div.2). To the extent that the EpiDoc ODD and schema have been customized and amount to transformative versions of the original schema, they are copyright Gabriel Bodard and the other contributors (as listed in tei:revisionDesc). See LICENSE.txt for license details.
