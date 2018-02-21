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

    def assertSubset(self, member, container, message):
        self.assertTrue(
            set(member).issubset(set(container)), message
        )

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
        """ Test a run on the local error tests passages with console print

         This unit test should be used to check edge cases. Repo 2 is built for that
        """
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        status = HookTest.test.cmd(**vars(HookTest.cmd.parse_args([
            "./tests/repo2",
            "--scheme", "epidoc", "--verbose",
            "--json", "cloning_dir/repo2.json"
        ])))
        parsed = self.read_logs("cloning_dir/repo2.json")
        ####
        #
        #   Test on tlg2255.perseus001
        #   With MyCapytain 0.0.9, display wrong number of passages in verbose
        #
        ####
        text = self.filter(parsed, "/data/tlg2255/perseus001/tlg2255.perseus001.perseus-grc1.xml")
        self.assertIn('>>>>>> 21 found', text["logs"], "Text should have 21 passages")
        self.assertTrue(text["status"], "Text tlg2255.p001.grc1 should pass")

        ####
        #
        #   Test on subreference
        #   Reference should make an issue
        #
        ####
        text = self.filter(parsed, "/data/tlg2255/perseus001/subreference.xml")
        self.assertFalse(text["units"]["URN informations"], "URN information fails")
        self.assertIn(">>>>>> Reference not accepted in URN", text["logs"], "URN Reference error should display in logs")
        self.assertFalse(text["status"], "Text subreference should fail because of URN")

        ####
        #
        #   Test on false.xml
        #   Is bad formatted XML + provoke a fatal in RNG
        #
        ####
        text = self.filter(parsed, "/data/tlg2255/perseus001/false.xml")
        self.assertFalse(text["status"], "Text false.xml should not pass")
        self.assertFalse(text["units"]["File parsing"], "It should not be parsable")
        self.assertIn(
            '>>>>>> fatal: The element type "text" must be terminated by the matching end-tag "</text>". [In (L236 C22)]',
            text["logs"], "Fatal error should be parsed"
        )

        ####
        #
        #   /data/stuff/__cts__.xml
        #   Has wrong root node
        #
        ####
        text = self.filter(parsed, "/data/stuff/__cts__.xml")
        self.assertSubset(
            [
                '>>>>>> No metadata type detected (neither work nor textgroup)',
                '>>>>>> Inventory can\'t be read through Capitains standards'
             ],
            text["logs"], "Absence of metadatafile should be spotted"
        )
        self.assertFalse(text["status"], "Wrong root node should fail file")

        ####
        #
        #   /data/capitainingest/tei2/tlg4089.tlg004.1st1k-grc1.xml
        #   Has wrong root node
        #
        ####
        text = self.filter(parsed, "/data/capitainingest/tei2/tlg4089.tlg004.1st1k-grc1.xml")
        self.assertEqual(
            {'Naming conventions': False, 'RefsDecl parsing': False, 'Epidoc DTD validation': False,
             'URN informations': False, 'File parsing': True, 'Passage level parsing': False,
             'Available in inventory': False, 'Unique nodes found by XPath': False,
             'Duplicate passages': False, 'Forbidden characters': False, 'Correct xml:lang attribute': False}
            ,
            text["units"], "Everything but XML parsing should fail in TEI.2 files"
        )
        self.assertFalse(text["status"], "Wrong XML scheme should fail file")

        ####
        #
        #   /data/wrongmetadata/__cts__xml
        #   Miss languages on groupname node and wrong path
        #
        ####
        text = self.filter(parsed, "/data/wrongmetadata/__cts__.xml")
        self.assertEqual(
            {'Metadata availability': False, 'URNs testing': True, 'MyCapytain parsing': True, 'File parsing': True,
             'Naming Convention': False}, text["units"],
            "Naming Convention should fail as well as lang"
        )
        self.assertSubset(
            [
                ">>>>>> 0 groupname found",
                ">>>>>> URN and path does not match"
            ], text["logs"], "Logs should be detailed when failing on lang or naming convention"
        )
        self.assertFalse(text["status"], "Missing language and naming convention should fail file")

        ####
        #
        #   /data/wrongmetadata/wrongmetadata/__cts__xml
        #   Miss languages on work node and wrong path
        #
        ####
        text = self.filter(parsed, "/data/wrongmetadata/wrongmetadata/__cts__.xml")
        self.assertEqual(
            {'Metadata availability': False, 'URNs testing': False, 'MyCapytain parsing': True, 'File parsing': True,
             'Naming Convention': False}, text["units"],
            "Naming Convention should fail as well as lang"
        )
        self.assertSubset(
            [
                ">>>>>> Work node is missing its lang attribute",
                ">>>>>> URN and path does not match"
            ], text["logs"], "Logs should be detailed when failing on lang or naming convention"
        )
        self.assertFalse(text["status"], "Missing language and naming convention should fail file")

    def test_run_local_console(self):
        """ Test a run on the local tests passages with console print """
        status, logs = self.hooktest(["./tests/repo1", "--console", "inline"])
        self.assertIn(
            "[failed] 3 out of 5 files did not pass the tests\n", logs,
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
        self.assertSubset(
            [
                ">>>> Testing /data/hafez/divan/__cts__.xml",
                ">>>> Testing /data/hafez/__cts__.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-far1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-eng1.xml",
                ">>>> Testing /hafez/divan/hafez.divan.perseus-ger1.xml"
            ],
            logs.split("\n"),
            "All files should be tested"
        )
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console_verbose(self):
        """ Test a run on the local tests passages with console print and verbose """
        status, logs = self.hooktest(["./tests/repo1", "--console", "inline", "--verbose"])
        self.assertIn(
            "[failed] 3 out of 5 files did not pass the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertIn(
            "\n>>>>>> ", logs,
            "Marker of verbose should be available"
        )
        self.assertSubset(
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
                ">>>>>> Edition, translation, and commentary urns : urn:cts:farsiLit:hafez.divan.perseus-far1 urn:cts:farsiLit:" + \
                "hafez.divan.perseus-eng1 urn:cts:farsiLit:hafez.divan.perseus-ger1",

            },
            logs.split("\n"),
            "All files should be tested and verbosed"
        )
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console_verbose_epidoc(self):
        """ Test a run on the local tests passages with console print as Epidoc """
        status, logs = self.hooktest(["./tests/repo1", "--console", "inline", "--verbose", "--scheme", "epidoc"])
        self.assertIn(
            ">>> [success] 0 out of 5 files did not pass the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertIn(
            "\n>>>>>> ", logs,
            "Marker of verbose should be available"
        )
        self.assertSubset(
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
                ">>>>>> Edition, translation, and commentary urns : urn:cts:farsiLit:hafez.divan.perseus-far1 urn:cts:farsiLit:" + \
                "hafez.divan.perseus-eng1 urn:cts:farsiLit:hafez.divan.perseus-ger1",

            },
            logs.split("\n"),
            "All files should be tested and verbosed"
        )
        self.assertEqual(status, "success", "Test should fail")

    def test_run_clone_empty(self):
        """ Test a clone on dummy empty repo """
        status, logs = self.hooktest(["./cloning_dir", "--repository", "Capitains/DH2016", "--console", "inline"])
        self.assertIn(
            ">>> [error] 0 out of 0 files did not pass the tests", logs,
            "No file should result in an [error] and no file tested"
        )

    def test_run_filter(self):
        """ Test a run on the local testFilers Repo with json

        """
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        status = HookTest.test.cmd(**vars(HookTest.cmd.parse_args([
            "./tests/repoFilters",
            "--scheme", "epidoc", "--verbose",
            "--json", "cloning_dir/repofilter.json",
            "--filter", "stoa0255.stoa004"
        ])))
        parsed = self.read_logs("cloning_dir/repofilter.json")
        self.assertEqual(len(parsed["units"]), 4, "There should be 4 tests : two texts, two metadata")

    def test_run_countwords(self):
        """ Test a run on the local with counting words with json

        """
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        status = HookTest.test.cmd(**vars(HookTest.cmd.parse_args([
            "./tests/repoFilters",
            "--scheme", "epidoc", "--verbose",
            "--json", "cloning_dir/repocount.json",
            "--filter", "stoa0255.stoa004",
            "--countwords"
        ])))
        parsed = self.read_logs("cloning_dir/repocount.json")
        self.assertEqual(
            sum([w["words"] for w in parsed["units"] if "words" in w]), 12830, "12830 Words should be found"
        )
        self.assertSubset(
            {
                '>>>>>> urn:cts:latinLit:stoa0255.stoa004.perseus-lat2 has 6415 words',
                '>>>>>> urn:cts:latinLit:stoa0255.stoa004.perseus-fre2 has 6415 words'
            }, [log for w in parsed["units"] if "words" in w for log in w["logs"]],
            "Check that logs print the number of words in verbose"
        )
        self.assertEqual(len(parsed["units"]), 4, "There should be 4 tests : two texts, two metadata")

    def test_run_tei_errors(self):
        """ Test a run on the local error TEI Repo with console print

         This unit test should be used to check edge cases. Repo tei is built for that
        """
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        status, logs = self.hooktest([
            "./tests/repotei", "--console", "inline",
            "--scheme", "tei", "--verbose",
            "--json", "cloning_dir/repotei.json"
        ])

        parsed = self.read_logs("cloning_dir/repotei.json")
        ####
        #
        #   Test on tei.tei.tei.xml
        #   Checks TEI RNG parsing
        #
        ####
        text = self.filter(parsed, "/data/tei/tei/tei.tei.tei.xml")
        self.assertIn(
            '>>>>>> error: element "varchar" not allowed anywhere [In (L3 C10)]', text["logs"],
            "TEI RNG Error should show"
        )
        self.assertFalse(text["status"], "Wrong TEI File should not pass")

        ####
        #
        #   Test on tei.tei.weirdurn.xml
        #   Weird URN Exception should be catched
        #
        ####
        text = self.filter(parsed, "/data/tei/tei/tei.tei.weirdurn.xml")
        self.assertIn(
            '>>>>>> error: element "encodingDesc" incomplete [In (L27 C20)]', text["logs"],
            "TEI RNG Error should show"
        )
        self.assertIn(
            ">>>>>> Elements of URN are empty: namespace, textgroup, version, work",
            text["logs"], "Empty member of urn should raise issue"
        )
        self.assertEqual(
            [False, False], [text["units"]["URN informations"], text["units"]["TEI DTD Validation"]], text["units"],
        )
        self.assertFalse(text["status"], "Wrong TEI File should not pass")

        ####
        #
        #   Test on tei/tei/__cts__.xml
        #   Weird URN Exception should be catched
        #
        ####
        text = self.filter(parsed, "/data/tei/tei/__cts__.xml")
        self.assertSubset(
            {
                '>>>>> URNs testing failed',
                ">>>>>> The Work URN is not a child of the Textgroup URN",
                ">>>>>> Text urn:cts:greekLit:tlg2255..perseus-grc1 URN is missing: work",
                ">>>>>> Text urn:cts:greekLit:tei.tei. URN is missing: version",
                ">>>>>> Text urn:cts:greekLit:tei.tei2.tei does not match parent URN",
                ">>>>>> There is different workUrns in the metadata"
            },
            text["logs"], "Details about failing URN should be provided"
        )
        self.assertFalse(text["status"], "Misformated URNS or not descendants should not pass")

    def test_run_clone_branch(self):
        """ Test a clone on dummy empty repo with branch change"""
        status, logs = self.hooktest([
            "./cloning_dir",
            "--repository", "Capitains/HookTest-TestRepo", "--branch", "master",
            "--console", "inline", "--verbose", "--scheme", "epidoc"
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
            "--console", "inline", "--verbose", "--scheme", "epidoc"
        ])
        self.assertIn(
            ">>> [success] 0 out of 5 files did not pass the tests\n", logs,
            "Test conclusion should be printed"
        )
        self.assertSubset(
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

            },
            logs.split("\n"),
            "All files should be tested and verbosed"
        )

    def test_run_local_greek(self):
        """ Test a run cloning a known working repository (PerseusDL/canonical-farsiLit)"""
        status, logs = self.hooktest([
            "./tests/greek", "--console", "inline", "--verbose", "--scheme", "epidoc"
        ])
        self.assertIn(
            ">>> [success] 0 out of 3 files did not pass the tests\n", logs,
            "Test conclusion should be printed"
        )

    def test_run_local_greek_count_word_raise(self):
        """ Test a run cloning a known working repository (PerseusDL/canonical-farsiLit)"""
        status, logs = self.hooktest([
            "./tests/test_count_words_not_break", "--console", "inline", "--verbose", "--scheme", "epidoc",
            "--verbose", "--manifest", "--countword", "--allowfailure"
        ])
        self.assertNotIn(
            "MyCapytain.errors.RefsDeclError", logs,
            "There should be no errors "
        )
        self.assertIn(
            "Word Counting", logs,
            "Word Counting should not be there"
        )
