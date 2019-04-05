import HookTest.test
import HookTest.cmd
from unittest import TestCase
from io import StringIO  # Python3
import json
import sys
import os
import shutil
import re
from colors import white, magenta
import os

def temp_dir_path(*args):
    """ Generate the temp directory path for given file"""
    return os.path.join(".", "cloning_dir", *args)


class TestProcess(TestCase):
    """
    Test HookTest as a complete process

    Thanks to http://stackoverflow.com/questions/18160078/how-do-you-write-tests-for-the-argparse-portion-of-a-python-module
    """
    def setUp(self):
        os.makedirs(temp_dir_path(), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(temp_dir_path())

    def assertLogResult(self, logs, left_column, right_column, message):
        """ Check that left column in logs has right column value

        :param logs: Logs to be checked
        :param left_column: Left Column content
        :param right_column: Right Column content
        :param message: Message to show for failure
        """
        self.assertRegex(logs, "\|\s+"+left_column+"\s+\|\s+" + right_column + "\s+\|", message)

    def parse_subset(self, logs, file):
        """

        :param logs:
        :param file:
        :return:
        """
        regex = re.compile(
            "(?:("+re.escape(white(file))+")|(" + re.escape(magenta(file)) + "))"  # Starts with the file name
            "\s+\|\s+([0-9;]+)\s+\|\s+"  # Nodes Count
            "([a-zA-Z0-9 \n\|\:\;]+)\+---"  # Colonnes
        )
        regex_tests = re.compile("(?:(?:\|\s+)+)?((?:[A-Za-z0-9:]+\s)+)")
        for _, match, nodes, text in regex.findall(logs):
            tests = [l.strip() for l in regex_tests.findall(text)]
            return nodes, tests

    def assertSubset(self, member, container, message):
        self.assertTrue(
            set(member).issubset(set(container)), message
        )

    def assertFailed(self, unit_logs, failed_test):
        self.assertIn(failed_test, unit_logs)

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
        #   Has wrong root node and a capitains_error
        #
        ####
        text = self.filter(parsed, "/data/capitainingest/tei2/tlg4089.tlg004.1st1k-grc1.xml")
        self.assertEqual(
            {'Naming conventions': False, 'RefsDecl parsing': False, 'Epidoc DTD validation': False,
             'URN informations': False, 'File parsing': False, 'Passage level parsing': False,
             'Available in inventory': False, 'Unique nodes found by XPath': False,
             'Duplicate passages': False, 'Forbidden characters': False, 'Correct xml:lang attribute': False,
             'Empty References': False}
            ,
            text["units"], "Everything should fail in TEI.2 files"
        )
        self.assertFalse(text["status"], "Wrong XML scheme should fail file")
        self.assertEqual(text['capitains_errors'], ['No reference declaration (refsDecl) found.'])

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
        status, logs = self.hooktest(["./tests/repo1", "--console", "--scheme", "tei"])
        self.assertIn(
            "..XXX\n", logs,
            "Test conclusion should be printed"
        )
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "3",
            "3 texts should be described in logs"
        )
        self.assertRegex(
            logs, "hafez\.divan\.perseus-far1\.xml",
            "Far1 file should be named"
        )
        self.assertRegex(
            logs, "hafez\.divan\.perseus-eng1\.xml",
            "eng1 file should be named"
        )
        self.assertRegex(
            logs, "hafez\.divan\.perseus-ger1\.xml",
            "ger1 file should be named"
        )
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console_verbose(self):
        """ Test a run on the local tests passages with console print and verbose """
        status, logs = self.hooktest(["./tests/repo1", "--console", "--verbose", "--scheme", "tei"])
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Metadata", "2",
            "2 metadata files should be passing in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "3",
            "3 texts should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Texts", "0",
            "3 texts should not be passing in logs"
        )

        node_count, unit = self.parse_subset(logs, "hafez.divan.perseus-far1.xml")
        self.assertEqual(
            node_count, "1;1;7;14",
            "Count of nodes should be displayed"
        )
        self.assertFailed(unit, "URN informations")
        self.assertEqual(status, "failed", "Test should fail")

    def test_run_local_console_verbose_epidoc(self):
        """ Test a run on the local tests passages with console print as Epidoc """
        status, logs = self.hooktest([
            "./tests/repo1", "--console", "--verbose", "--scheme", "epidoc"])
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Metadata", "2",
            "2 metadata files should be passing in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "3",
            "3 texts should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Texts", "3",
            "3 texts should not be passing in logs"
        )
        node_count, unit = self.parse_subset(logs, "hafez.divan.perseus-far1.xml")
        self.assertEqual(
            node_count, "1;1;7;14",
            "Count of nodes should be displayed"
        )
        self.assertEqual(status, "success", "Test should success")

    def test_run_local_console_verbose_auto_rng(self):
        """ Test a run on the local tests passages with console print while automatically detecting downloading the correct remote rng """
        status, logs = self.hooktest([
            "./tests/test_auto_rng", "--console", "--verbose", "--scheme", "auto", "--guidelines", "2.epidoc"])
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Metadata", "2",
            "2 metadata files should be passing in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "3",
            "3 texts should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Texts", "2",
            "2 texts should be passing in logs"
        )
        node_count, unit = self.parse_subset(logs, "hafez.divan.perseus-far1.xml")
        self.assertEqual(
            node_count, "1;1;7;14",
            "Correct node counts should be displayed for file using remote RNG"
        )

        node_count2, result = self.parse_subset(logs, "hafez.divan.perseus-ger1.xml")
        self.assertEqual(result, ['Automatic RNG validation'], "RNG validation should fail with invalid file path")

        self.assertEqual(status, "failed", "Test should fail")
        shutil.rmtree('./.rngs/')

    def test_run_local_console_verbose_no_scheme(self):
        """ Test a run on the local tests passages with console print with no RNG run """
        status, logs = self.hooktest([
            "./tests/test_repositories/test_wrong_tei", "--console", "--verbose", "--scheme", "ignore", "--guidelines", "2.epidoc"])
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Metadata", "2",
            "2 metadata files should be passing in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "1",
            "3 texts should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Texts", "1",
            "2 texts should be passing in logs"
        )
        node_count, unit = self.parse_subset(logs, "hafez.divan.perseus-ger1.xml")
        self.assertEqual(
            node_count, "1;1;7;28",
            "Correct node counts should be displayed for file using remote RNG"
        )

        self.assertEqual(status, "success", "Test should success")

    def test_run_local_console_verbose_path_to_rng_success(self):
        """ Test a run on the local tests passages with --scheme as local RNG path """
        status, logs = self.hooktest([
            "./tests/repo1", "--console", "--verbose", "--scheme", os.path.abspath("HookTest/resources/epidoc.rng"), "--guidelines", "2.epidoc"])
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Metadata", "2",
            "2 metadata files should be passing in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "3",
            "3 texts should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Texts", "3",
            "3 texts should not be passing in logs"
        )
        node_count, unit = self.parse_subset(logs, "hafez.divan.perseus-far1.xml")
        self.assertEqual(
            node_count, "1;1;7;14",
            "Count of nodes should be displayed"
        )
        self.assertEqual(status, "success", "Test should success")

    def test_run_local_console_verbose_path_to_rng_failure(self):
        """ Test a run on the local tests passages with --scheme as wrong local RNG path """
        message = """--scheme must either point to an existing local RNG file or be one of the following:
 tei: Use the most recent TEI-ALL DTD
epidoc: Use the most recent epiDoc DTD
ignore: Perform no schema validation
auto: Automatically detect the RNG to use from the xml-model declaration in each individual XML file"""
        with self.assertRaises(BaseException, msg=message) as cm:
            status, logs = self.hooktest([
                "./tests/repo1", "--console", "--verbose", "--scheme", os.path.abspath("wrong/path"), "--guidelines", "2.epidoc"])

    def test_run_local_console_verbose_remote_download_timeout_and_use_existing_rng(self):
        """ Test that the download of a remote RNG will timeout after the period set in the --timeout argument
            And then est that a run with --scheme auto will use an existing local download if it has previously been downloaded
            I have joined these two tests because I think Travis runs them concurrently and one interferes with the other
        """
        os.makedirs('.rngs', exist_ok=True)
        with open('.rngs/af2245c1fd91fabf76516bb0b9332a90.rng-indownload', mode="w") as f:
            f.write("Downloading...")
        message = "The download of the RNG took too long"
        status, logs = self.hooktest([
            "./tests/test_auto_rng", "--console", "--verbose", "--scheme", 'auto', "--guidelines", "2.epidoc", "--timeout", "1"])
        self.assertIn('OSError: The download of the RNG took too long', logs, "The Error should show up in the logs")
        shutil.rmtree('./.rngs')
        os.makedirs('.rngs', exist_ok=True)
        with open('.rngs/af2245c1fd91fabf76516bb0b9332a90.rng', mode="w") as f:
            f.write("Downloading...")
        status, logs = self.hooktest([
            "./tests/test_auto_rng", "--console", "--verbose", "--scheme", 'auto', "--guidelines", "2.epidoc", "--timeout", "1"])
        self.assertIn("fatal: Content is not allowed in prolog. [In (L1 C1)]", logs,
                      "Since the created RNG file has no content, this error shows that this RNG was used.")
        shutil.rmtree('./.rngs')

    def test_run_filter(self):
        """ Test a run on the local testFilers Repo with json

        """
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        json_file = temp_dir_path("repofilter.json")
        status = HookTest.test.cmd(**vars(HookTest.cmd.parse_args([
            "./tests/repoFilters",
            "--scheme", "epidoc", "--verbose",
            "--json", json_file,
            "--filter", "stoa0255.stoa004"
        ])))
        parsed = self.read_logs(json_file)
        self.assertEqual(len(parsed["units"]), 4, "There should be 4 tests : two texts, two metadata")

    def test_run_countwords(self):
        """ Test a run on the local with counting words with json

        """
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        json_file = temp_dir_path("repocount.json")
        status = HookTest.test.cmd(**vars(HookTest.cmd.parse_args([
            "./tests/repoFilters",
            "--scheme", "epidoc", "--verbose",
            "--json", json_file,
            "--filter", "stoa0255.stoa004",
            "--countwords"
        ])))
        parsed = self.read_logs(json_file)
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
        json_file = temp_dir_path("repotei.json")
        # Can be replace by HookTest.test.cmd(**vars(HookTest.cmd.parse_args()) for debug
        status, logs = self.hooktest([
            "./tests/repotei", "--console",
            "--scheme", "tei", "--verbose",
            "--json", json_file
        ])

        parsed = self.read_logs(json_file)
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
        #   Weird URN Exception should be caught
        #
        ####
        text = self.filter(parsed, "/data/tei/tei/tei.tei.weirdurn.xml")
        self.assertIn(
            '>>>>>> error: element "fileDesc" incomplete [In (L10 C16)]', text["logs"],
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
        #   Weird URN Exception should be caught
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
        self.assertFalse(text["status"], "Wrongly formated URNS or not descendants should not pass")

    def test_run_local_greek(self):
        """ Test a run cloning a known working repository (PerseusDL/canonical-farsiLit)"""
        status, logs = self.hooktest([
            "./tests/greek", "--console", "--verbose", "--scheme", "epidoc"
        ])
        self.assertLogResult(
            logs, "Metadata Files", "2",
            "2 metadata files should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Metadata", "2",
            "2 metadata files should be passing in logs"
        )
        self.assertLogResult(
            logs, "Total Texts", "1",
            "3 texts should be described in logs"
        )
        self.assertLogResult(
            logs, "Passing Texts", "1",
            "3 texts should not be passing in logs"
        )

    def test_run_local_greek_count_word_raise(self):
        """ Test a run cloning a known working repository (PerseusDL/canonical-farsiLit)"""
        status, logs = self.hooktest([
            "./tests/test_count_words_not_break", "--console", "--verbose", "--scheme", "epidoc",
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
