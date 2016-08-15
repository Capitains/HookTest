import HookTest.test
import HookTest.cmd
from unittest import TestCase
from io import StringIO  # Python3

import sys


class TestProcess(TestCase):
    """
    Test HookTest as a complete process

    Thanks to http://stackoverflow.com/questions/18160078/how-do-you-write-tests-for-the-argparse-portion-of-a-python-module
    """

    def hooktest(self, args):
        """ Run args (Splitted list of command line)

        ..note:: See https://wrongsideofmemphis.wordpress.com/2010/03/01/store-standard-output-on-a-variable-in-python/

        :param args: List of commandline arguments
        :return: Sys stdout, status
        """
        # Store the reference, in case you want to show things again in standard output
        old_stdout = sys.stdout
        # This variable will store everything that is sent to the standard output
        result = StringIO()
        sys.stdout = result
        # Here we can call anything we like, like external modules, and everything
        # that they will send to standard output will be stored on "result"
        status = HookTest.test.cmd(**vars(HookTest.cmd.parse_args(args)))
        # Redirect again the std output to screen
        sys.stdout = old_stdout

        # Then, get the stdout like a string and process it!
        result_string = result.getvalue()
        return status, result_string

    def test_run_local_no_option(self):
        """ Test a run on the local tests passages """
        status, logs = self.hooktest(["./tests"])
        self.assertEqual(len(logs), 0, "There should be no logs")
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console(self):
        """ Test a run on the local tests passages with console print """
        status, logs = self.hooktest(["./tests", "--console"])
        self.assertIn(
            "[failed] 2 over 5 texts have fully passed the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertIn(
            ">>>>> Metadata availability passed", logs,
            "Metadata file should be parsed"
        )
        self.assertIn(
            "Unique nodes found by XPath passed", logs,
            "Normal file should be tested"
        )
        self.assertTrue(
            set([
                ">>>> Testing /data/hafez/divan/__cts__.xml",
                ">>>> Testing /data/hafez/__cts__.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-far1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-eng1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-ger1.xml"
            ]).issubset(set(logs.split("\n"))),
            "All files should be tested"
        )
        self.assertEqual(status, "failed", "Test should fail")
