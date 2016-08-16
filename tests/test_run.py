import HookTest.test
import HookTest.cmd
from unittest import TestCase
from io import StringIO  # Python3
import json
import sys


class TestProcess(TestCase):
    """
    Test HookTest as a complete process

    Thanks to http://stackoverflow.com/questions/18160078/how-do-you-write-tests-for-the-argparse-portion-of-a-python-module
    """
    def read_logs(self, file):
        j = []
        with open(file) as file:
            j = json.load(file)
        return j

    def filter(self, obj, name):
        return [x for x in obj["units"] if x["name"] == name][0]

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
        status, logs = self.hooktest(["./tests/repo1"])
        self.assertEqual(len(logs), 0, "There should be no logs")
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_repo_errors(self):
        """ Test a run on the local tests passages with console print

         This unit test should be used to check edge cases. Repo 2 is built for that
        """
        status, logs = self.hooktest([
            "./tests/repo2", "--console",
            "--scheme", "epidoc", "--verbose",
            "--json", "cloning_dir/repo2.json"
        ])
        parsed = self.read_logs("cloning_dir/repo2.json")
        ####
        #
        #   Test on tlg2255.perseus001
        #   With MyCapytain 0.0.9, display wrong number of passages in verbose
        #
        ####
        text = self.filter(parsed, "/data/tlg2255/perseus001/tlg2255.perseus001.perseus-grc1.xml")
        self.assertIn('>>>>>> 2 found', text["logs"], "Text should have 22 passages")
        self.assertTrue(text["status"], "Text tlg2255.p001.grc1 should pass")

        ####
        #
        #   Test on false.xml
        #   Is bad formatted XML + provoke a fatal in RNG
        #
        ####
        text = self.filter(parsed, "/data/tlg2255/perseus001/false.xml")
        self.assertFalse(text["status"], "Text tlg2255.p001.grc1 should not pass")
        self.assertFalse(text["units"]["File parsing"], "It should not be parsable")
        self.assertIn(
            '>>>>>> fatal: The element type "text" must be terminated by the matching end-tag "</text>". [In (L236 C22)]',
            text["logs"][-1], "Fatal error should be parsed"
        )

        ####
        #
        #   /data/stuff/__cts__.xml
        #   Has wrong root node
        #
        ####
        text = self.filter(parsed, "/data/stuff/__cts__.xml")
        self.assertIn(
            '>>>>>> No metadata type detected (neither work nor textgroup)\n>>>>>> Inventory can\'t '\
            'be read through Capitains standards',
            text["logs"], "Fatal error should be parsed"
        )
        self.assertFalse(text["status"], "Wrong root node should fail file")

    def test_run_local_console(self):
        """ Test a run on the local tests passages with console print """
        status, logs = self.hooktest(["./tests/repo1", "--console"])
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
            {
                ">>>> Testing /data/hafez/divan/__cts__.xml",
                ">>>> Testing /data/hafez/__cts__.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-far1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-eng1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-ger1.xml"
            }.issubset(set(logs.split("\n"))),
            "All files should be tested"
        )
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console_verbose(self):
        """ Test a run on the local tests passages with console print """
        status, logs = self.hooktest(["./tests/repo1", "--console", "--verbose"])
        self.assertIn(
            "[failed] 2 over 5 texts have fully passed the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertIn(
            "\n>>>>>> ", logs,
            "Marker of verbose should be available"
        )
        self.assertTrue(
            {
                # List of file tested
                ">>>> Testing /data/hafez/divan/__cts__.xml",
                ">>>> Testing /data/hafez/__cts__.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-far1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-eng1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-ger1.xml",

                # Tests number of nodes showing
                ">>>>>> 32 found",
                ">>>>>> 498 found",
                ">>>>>> 4243 found",
                ">>>>>> 13613 found",

                # RefsDecl verbosing should match
                ">>>>> RefsDecl parsing passed",
                ">>>>>> 4 citation's level found",

                # URN Should fail because we are using TEI scheme by default
                ">>>>> URN informations failed",

                # Metadata information found
                ">>>>>> Group urn : urn:cts:farsiLit:hafez",
                ">>>>>> Work urn : urn:cts:farsiLit:hafez.divan",
                ">>>>>> Editions and translations urns : urn:cts:farsiLit:hafez.divan.perseus-far1 urn:cts:farsiLit:" + \
                "hafez.divan.perseus-eng1 urn:cts:farsiLit:hafez.divan.perseus-ger1",

                }.issubset(set(logs.split("\n"))),
            "All files should be tested and verbosed"
        )
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console_verbose_epidoc(self):
        """ Test a run on the local tests passages with console print """
        status, logs = self.hooktest(["./tests/repo1", "--console", "--verbose", "--scheme", "epidoc"])
        self.assertIn(
            "[success] 5 over 5 texts have fully passed the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertIn(
            "\n>>>>>> ", logs,
            "Marker of verbose should be available"
        )
        self.assertTrue(
            {
                # List of file tested
                ">>>> Testing /data/hafez/divan/__cts__.xml",
                ">>>> Testing /data/hafez/__cts__.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-far1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-eng1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-ger1.xml",

                # Tests number of nodes showing
                ">>>>>> 32 found",
                ">>>>>> 498 found",
                ">>>>>> 4243 found",
                ">>>>>> 13613 found",

                # RefsDecl verbosing should match
                ">>>>> RefsDecl parsing passed",
                ">>>>>> 4 citation's level found",

                # URN Should fail because we are using Epidoc scheme here
                ">>>>> URN informations passed",

                # Metadata information found
                ">>>>>> Group urn : urn:cts:farsiLit:hafez",
                ">>>>>> Work urn : urn:cts:farsiLit:hafez.divan",
                ">>>>>> Editions and translations urns : urn:cts:farsiLit:hafez.divan.perseus-far1 urn:cts:farsiLit:" + \
                "hafez.divan.perseus-eng1 urn:cts:farsiLit:hafez.divan.perseus-ger1",

                }.issubset(set(logs.split("\n"))),
            "All files should be tested and verbosed"
        )
        self.assertEqual(status, "success", "Test should fail")

    def test_run_clone_empty(self):
        """ Test a clone on dummy empty repo """
        status, logs = self.hooktest(["./cloning_dir", "--repository", "Capitains/DH2016", "--console"])
        self.assertIn(
            ">>> [error] 0 over 0 texts have fully passed the tests", logs,
            "No file should result in no file tested"
        )

    def test_run_clone_branch(self):
        """ Test a clone on dummy empty repo with branch change"""
        status, logs = self.hooktest([
            "./cloning_dir",
            "--repository", "Capitains/HookTest-TestRepo", "--branch", "master",
            "--console", "--verbose", "--scheme", "epidoc"
        ])
        setlogs = set(logs.split("\n"))

        self.assertTrue(
            {
                ">>>>> Epidoc DTD validation failed",
                ">>>>>> error: element \"seg\" not allowed here [In (L43 C32)]",
                ">>>>>> error: element \"table\" not allowed anywhere [In (L31 C51)]"
            }.issubset(setlogs),
            "Logs should fail on Epidoc wrong"
        )

        self.assertTrue(
            {
                ">>>>>> Duplicate references found : 1.1"
            }.issubset(setlogs),
            "Duplicate note should be explicit"
        )
        self.assertIn(
            ">>>>> Passage level parsing passed\n>>>>>> 1 found\n>>>>>> 32 found", logs,
            "Ger2 should success in passage number "
        )

    def test_run_clone_farsiLit(self):
        """ Test a run cloning a known working repository (PerseusDL/canonical-farsiLit)"""
        status, logs = self.hooktest([
            "./cloning_dir", "--repository", "PerseusDL/canonical-farsiLit",
            "--console", "--verbose", "--scheme", "epidoc"
        ])
        self.assertIn(
            "[success] 5 over 5 texts have fully passed the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertTrue(
            {
                # List of file tested
                ">>>> Testing PerseusDL/canonical-farsiLit/data/hafez/__cts__.xml",
                ">>>> Testing PerseusDL/canonical-farsiLit/data/hafez/divan/__cts__.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-far1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-eng1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-ger1.xml",

                # Tests number of nodes showing
                ">>>>>> 32 found",
                ">>>>>> 498 found",
                ">>>>>> 4243 found",
                ">>>>>> 13613 found",

                # RefsDecl verbosing should match
                ">>>>> RefsDecl parsing passed",
                ">>>>>> 4 citation's level found",

                # URN Should fail because we are using Epidoc scheme here
                ">>>>> URN informations passed",

                # Metadata information found
                ">>>>>> Group urn : urn:cts:farsiLit:hafez",
                ">>>>>> Work urn : urn:cts:farsiLit:hafez.divan"

            }.issubset(set(logs.split("\n"))),
            "All files should be tested and verbosed"
        )
