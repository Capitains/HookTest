HookTest API Documentation
==========================

Library Structure
#################

The library is divided in three different modules :
- **cmd** is the module for running HookTest in command line.
- **test** is the module for the main pipeline : it takes care of finding the files to test, dispatchinmg the test on them and interpret them
- **units** is the module for each specific filetype test : it contains the logic of tests for individual files

Commands
########

.. autofunction:: HookTest.cmd.parse_args

.. autofunction:: HookTest.cmd.cmd

Test Pipeline
#############

Files Finders
*************

.. autoclass:: HookTest.test.DefaultFinder
    :members:

.. autoclass:: HookTest.test.FilterFinder
    :members:

Pipeline
********

.. autoclass:: HookTest.test.Test
    :members:

.. autofunction:: HookTest.test.cmd


Models
******

.. autoclass:: HookTest.test.Progress
    :members:

.. autoclass:: HookTest.test.UnitLog
    :members:

Test units
##########

.. autoclass:: HookTest.units.TESTUnit
    :members:

.. autoclass:: HookTest.capitains_units.cts.CTSMetadata_TestUnit
    :members:

.. autoclass:: HookTest.capitains_units.cts.CTSText_TestUnit
    :members:
