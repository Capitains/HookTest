import unittest
import HookTest.test
import HookTest.units
import mock
import json
from multiprocessing.pool import Pool
from collections import OrderedDict
import shutil
import os


def unitlog_dict():
    with mock.patch("HookTest.test.time.strftime", return_value="Time"):
        a = ((
            "001", HookTest.test.UnitLog(
                directory=".",
                name="001",
                units={},
                coverage=100.0,
                status=True
            )), (
            "002", HookTest.test.UnitLog(
                directory=".",
                name="002",
                units={},
                coverage=50.0,
                status=False
            ))
        )
    return OrderedDict(a)


class TestTest(unittest.TestCase):
    TESTDIR = 'currentTest/'

    def setUp(self):
        self.test = HookTest.test.Test(
            "./",
            repository="PerseusDL/tests",
            branch="refs/heads/dev",
            uuid="1234",
            ping="http://services.perseids.org/Hook",
            secret="PerseusDL"
        )
        self.test_print = HookTest.test.Test(
            "./",
            repository="PerseusDL",
            branch="refs/heads/master",
            uuid="1234",
            secret="PerseusDL"
        )

    def tearDown(self):
        if os.path.isdir(self.TESTDIR):
            shutil.rmtree(self.TESTDIR)

    def createTestDir(self, d):
        """ Creates directory to test file system actions

        :param d: the source directory to be copied
        :type d: str
        """
        shutil.copytree(d, self.TESTDIR)

    def test_init_conditions(self):
        """ Try special case of init """
        a = HookTest.test.Test("", triggering_size=10)
        self.assertEqual(a.triggering_size, 10)

        with self.assertRaises(ValueError):
            HookTest.test.Test(".", scheme="html")

    def test_files_properties(self):
        """ Test different files properties
        """
        a = HookTest.test.Test("")
        a.text_files, a.cts_files = ["a text"]*7, ["a cts metadata file"]*5
        self.assertEqual(a.files, (["a text"]*7, ["a cts metadata file"]*5))
        self.assertEqual(a.count_files, 12)

    def test_triggering_size(self):
        """ Test triggering size is defaulted when possible """

        # When triggering size is set by user
        a = HookTest.test.Test("", triggering_size=10)
        self.assertEqual(a.triggering_size, 10)

        # When percentage is higher than default
        a = HookTest.test.Test("")
        a.text_files, a.cts_files = ["a text"]*200, ["a cts metadata file"]*200
        self.assertEqual(a.triggering_size, 20)

        # Default
        a = HookTest.test.Test("")
        a.text_files, a.cts_files = ["a text"]*10, ["a cts metadata file"]*10
        self.assertEqual(a.triggering_size, HookTest.test.Test.STACK_TRIGGER_SIZE)

    def test_dump(self):
        """ Check that light json is sent
        """
        self.assertEqual(
            HookTest.test.Test.dump({"Test": 1, "File": "file.xml"}),
            '{"File":"file.xml","Test":1}'
        )

    @mock.patch('HookTest.test.print', create=True)
    def test_log(self, mocked):
        """ Test logging function """

        # When print is not set to True and there is not ping
        self.test_print.log("This is a log")
        self.assertEqual(len(mocked.mock_calls), 0)

        # Test when print
        self.test_print.console = "inline"
        self.test_print.log("This is a log")
        mocked.assert_called_with("This is a log", flush=True)

        with mock.patch('HookTest.test.sys', create=True) as sysout:
            # Test when print Unit Log
            logs = unitlog_dict()
            self.test_print.console = "table"
            self.test_print.log(logs["001"])
            sysout.stdout.write.assert_called_with(".")
            sysout.stdout.flush.assert_called_with()
            self.test_print.log(logs["002"])
            sysout.stdout.write.assert_called_with("X")
            sysout.stdout.flush.assert_called_with()

        logs = unitlog_dict()
        a = HookTest.test.Test("", ping="Http", triggering_size=2)
        flush = mock.MagicMock()
        a.flush = flush
        a.log(logs["001"])
        self.assertEqual(len(mocked.mock_calls), 1)
        self.assertEqual(len(flush.mock_calls), 0)
        a.results = logs
        a.log(logs["002"])
        self.assertEqual(len(mocked.mock_calls), 1)
        flush.assert_called_with(list(logs.values()))

    @mock.patch('HookTest.test.print', create=True)
    def test_start(self, printed):
        """ Testing start function, which is notification related
        """
        # With HTTP
        send = mock.MagicMock()
        print(self.test.console)
        self.test.send = send
        self.test.text_files, self.test.cts_files = ["a text"]*5, ["a cts metadata file"]*2
        self.test.start()
        send.assert_called_with({
            "logs": [
                ">>> Starting tests !"
            ],
            "files": 7,
            "texts": 5,
            "inventories": 2,
        })

        # With not print
        self.test_print.start()
        self.assertEqual(len(printed.mock_calls), 0, msg="Default of start is not to print")

        # With print
        self.test_print.console = "inline"
        self.test_print.text_files, self.test_print.cts_files = ["a text"]*5, ["a cts metadata file"]*2
        self.test_print.start()
        self.assertEqual(len(printed.mock_calls), 2, msg="Start should print twice")
        printed.assert_has_calls([
            mock.call('>>> Starting tests !', flush=True),
            mock.call(">>> Files to test : 7", flush=True)
        ])

    @mock.patch('HookTest.test.print', create=True)
    def test_end(self, printed):
        """ Testing end function, which is notification related
        """
        # With HTTP
        send = mock.MagicMock()
        self.test.send = send
        self.test.text_files, self.test.cts_files = ["001"], ["002"]
        results = unitlog_dict()
        self.test.results = results
        self.test.passing = {"001": True, "002": False}
        self.test.end()
        send.assert_called_with({
            "status": "failed",
            "coverage": 75.00,
            "units": [r.dict for r in results.values()]
        })

        # With not print
        self.test_print.end()
        self.assertEqual(len(printed.mock_calls), 0, msg="Default of start is not to print")

        # With print
        self.test_print.console = "inline"
        self.test_print.text_files, self.test_print.cts_files = ["a text"]*5, ["a cts metadata file"]*2
        self.test_print.passing = {
            1: True,
            2: True,
            3: True,
            4: True,
            5: True,
            6: False,
            7: False
        }
        self.test_print.end()
        self.assertEqual(len(printed.mock_calls), 1, msg="End should print once")
        printed.assert_called_with(
            ">>> End of the test !\n>>> [failed] 2 out of 7 files did not pass the tests", flush=True
        )

    @mock.patch('HookTest.test.print', create=True)
    def test_download(self, printed):
        self.test_print.download()
        self.assertEqual(len(printed.mock_calls), 0, msg="When print is not set, nothing is shown")

        self.test.download()
        self.assertEqual(len(printed.mock_calls), 0, msg="When print is not set, nothing is shown [Neither with Ping]")

        self.test_print.console = "inline"
        self.test_print.verbose = 10
        self.test_print.progress = HookTest.test.Progress()
        self.test_print.progress.download = "55 kb/s"
        self.test_print.download()
        printed.assert_called_with(
            "Cloning repository\nDownloaded 0/0 (55 kb/s)",
            flush=True
        )

    @mock.patch('HookTest.test.send', create=True)
    def test_flush(self, mocked):
        """ Test the flush method, which sends the remaining logs to be treated
        """
        self.test.send = mocked

        #  Empty flushing
        self.test.flush(self.test.stack)
        self.assertEqual(len(mocked.mock_calls), 0)

        # Test with nothing sent
        results = unitlog_dict()
        self.test.results = results
        self.test.flush(self.test.stack)
        mocked.assert_called_with({"units": [n.dict for n in results.values()]})

        # Test after sent has been updated
        self.test.flush(self.test.stack)
        self.assertEqual(len(mocked.mock_calls), 1)

        # Test when partially sent
        results = unitlog_dict()
        self.test.results = results
        self.test.results["002"].sent = True
        self.test.flush(self.test.stack)
        mocked.assert_called_with({"units": [results["001"].dict]})

    def test_stack(self):
        """ Test the stack property """
        self.test.results = {}
        self.assertEqual(self.test.stack, [], msg="When no result available, stack is empty")

        results = unitlog_dict()
        self.test.results = results
        self.assertEqual(
            self.test.stack,
            list(results.values()),
            msg="When no result has been sent, stack containing everything"
        )

        results = unitlog_dict()
        self.test.results = results
        self.test.results["002"].sent = True
        self.assertEqual(
            self.test.stack,
            [results["001"]],
            msg="When 1 result has been sent, it should not be in stack"
        )

    @mock.patch('HookTest.test.requests.post', create=True)
    def test_send(self, mocked):
        """ Test printing function """
        self.test.send(["5"] * 50)

        data = HookTest.test.Test.dump({"logs": ["5"] * 50})
        mocked.assert_called_with(
            "http://services.perseids.org/Hook",
            data=bytes(data, "utf-8"),
            headers={
                "HookTest-Secure-X": "587f69e2e316c5da00d3bdde1b9f6a66632b9ea2",
                'HookTest-UUID': '1234'
            }
        )

        data = HookTest.test.Test.dump({"this": "is a dict"})
        self.test.send({"this": "is a dict"})
        mocked.assert_called_with(
            "http://services.perseids.org/Hook",
            data=bytes(data, "utf-8"),
            headers={
                "HookTest-Secure-X": "46e8b5645de78bdcf3bad24e4f3ca5d7de95b01e",
                'HookTest-UUID': '1234'
            }
        )

    def test_successes(self):
        """ Test successes property
        """
        self.test.passing = {"1": True, "2": True, "3": False}
        self.assertEqual(self.test.successes, 2)
        self.test.passing = {"1": True, "2": False, "3": False}
        self.assertEqual(self.test.successes, 1)
        self.test.passing = {}
        self.assertEqual(self.test.successes, 0)

    def test_status(self):
        """ Check that finishes return a consistent status
        """
        self.test.passing = {"001": True}
        self.test.text_files = [1]
        self.test.cts_files = [1]

        self.assertEqual(self.test.status, "error")  # 1/2 tested

        self.test.passing["002"] = False
        self.assertEqual(self.test.status, "failed")  # 1/2 successes
        self.test.passing["002"] = True
        self.assertEqual(self.test.status, "success")  # 2/2 successes
        self.test.text_files, self.test.cts_files = [], []
        self.assertEqual(self.test.status, "error")  # 0 Files

    def test_json(self):
        """ Check that json return is stable
        """
        report = json.dumps({
            "status": "failed",
            "units": [{
                    "at": "Time",
                    "coverage": 100.0,
                    "logs": [],
                    "name": "001",
                    "status": True,
                    "units": {}
                },
                {
                    "at": "Time",
                    "coverage": 50.0,
                    "logs": [],
                    "name": "002",
                    "status": False,
                    "units": {}
                }
            ],
            "coverage": 75.0
        }, sort_keys=True, separators=(",", ":"))
        self.test.cts_files, self.test.text_files = [1], [1]
        self.test.passing = {"001": True, "002": False}
        self.test.results = unitlog_dict()
        self.assertEqual(self.test.json, report)

    def test_directory(self):
        """ Check the directory forming
        """
        self.test.repository = False
        self.assertEqual(self.test.directory, "./")
        self.test.repository = "PerseusDL/canonical-farsiLit"
        self.test.uuid = None
        self.assertEqual(self.test.directory, "./canonical-farsiLit")
        self.test.uuid = "1234"
        self.assertEqual(self.test.directory, "./1234")

    @mock.patch("HookTest.test.time.strftime", return_value="Time")
    def test_unit_inv_verbose(self, time_mocked):
        """ Test unit when __cts__.xml """
        test = mock.MagicMock()
        test.return_value = [
            ("MyCapytain", True, []),
            ("Folder Name", False, ["It should be in a subfolder"])
        ]
        INVObject = mock.Mock(
            test=test,
            urns=["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        )
        invunit = mock.Mock(
            return_value=INVObject
        )
        self.test.verbose = True
        with mock.patch("HookTest.test.HookTest.capitains_units.cts.CTSMetadata_TestUnit", invunit):
            logs, filepath, additional = self.test.unit("__cts__.xml")
            self.assertIn(">>>> Testing __cts__.xml", logs.logs)
            self.assertIn(">>>>> MyCapytain passed", logs.logs)
            self.assertIn(">>>>> Folder Name failed", logs.logs)
            self.assertIn("It should be in a subfolder", logs.logs)
            self.assertIn("urn:cts:latinLit:phi1294.phi002.perseus-lat2", additional)
            self.test.results[filepath] = logs

            self.assertEqual(self.test.results["__cts__.xml"].dict, {
                'at' : 'Time',
                'name': "__cts__.xml",
                'coverage': 50.0,
                'status': False,
                'units': {
                    'Folder Name': False,
                    'MyCapytain': True
                },
                "logs": [
                    ">>>> Testing __cts__.xml",
                    ">>>>> MyCapytain passed",
                    ">>>>> Folder Name failed",
                    "It should be in a subfolder"
                ]
            })
            self.assertEqual(self.test.passing["__cts__.xml"], False)
            self.assertEqual(logs, self.test.results["__cts__.xml"])

    @mock.patch("HookTest.test.time.strftime", return_value="Time")
    def test_unit_inv_non_verbose(self, mocked_time):
        """ Test unit when __cts__.xml """
        test = mock.MagicMock()
        test.return_value = [
            ("MyCapytain", True, []),
            ("Folder Name", True, ["It should be in a subfolder"])
        ]
        INVObject = mock.Mock(
            test=test,
            urns=["urn:cts:latinLit:phi1294.phi002.perseus-lat2"]
        )
        invunit = mock.Mock(
            return_value=INVObject
        )
        with mock.patch("HookTest.test.HookTest.capitains_units.cts.CTSMetadata_TestUnit", invunit):
            logs, filepath, additional = self.test.unit("/phi1294/phi002/__cts__.xml")
            self.assertIn(">>>> Testing /phi1294/phi002/__cts__.xml", logs.logs)
            self.assertIn(">>>>> MyCapytain passed", logs.logs)
            self.assertIn(">>>>> Folder Name passed", logs.logs)
            self.assertIn("urn:cts:latinLit:phi1294.phi002.perseus-lat2", additional)
            self.test.results[filepath] = logs

            self.assertEqual(self.test.results["/phi1294/phi002/__cts__.xml"].dict, {
                'at': 'Time',
                'name': "/phi1294/phi002/__cts__.xml",
                'coverage': 100.0,
                'status': True,
                'units': {
                    'Folder Name': True,
                    'MyCapytain': True
                },
                "logs": [
                    ">>>> Testing /phi1294/phi002/__cts__.xml",
                    ">>>>> MyCapytain passed",
                    ">>>>> Folder Name passed"
                ]
            })

            self.assertEqual(logs.status, True)
            self.assertEqual(logs, self.test.results["/phi1294/phi002/__cts__.xml"])

    @mock.patch("HookTest.test.time.strftime", return_value="Time")
    def test_unit_text_mute(self, time_mocked):
        # test is the mocked 'test' method of the unit
        test = mock.MagicMock()
        test.return_value = [
            ("MyCapytain", True, []),
            ("Folder Name", True, ["It should be in a subfolder"])
        ]
        # UnitInstance is a mock which has a test method is a mock
        UnitInstance = mock.Mock(
            test=test, forbiddens=['forbid'], duplicates=['duplicate'], citation=['citation'], lang="grc",
            dtd_errors=['dtd_errors']
        )
        # ctsunit is a mock of the class CTSText_TestUnit and will return the instance UnitInstance
        ctsunit = mock.Mock(
            return_value=UnitInstance
        )
        with mock.patch("HookTest.test.HookTest.capitains_units.cts.CTSText_TestUnit", ctsunit):
            logs, filepath, additional = self.test.unit("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml")
            ctsunit.assert_called_with("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml", countwords=False, timeout=30)
            self.assertIn(">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml", logs.logs)
            self.assertIn(">>>>> MyCapytain passed", logs.logs)
            self.assertIn(">>>>> Folder Name passed", logs.logs)
            self.test.results[filepath] = logs

            self.assertEqual(self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"].dict, {
                'name': '/phi1294/phi002/phi1294.phi002.perseus-lat2.xml',
                'at': 'Time',
                'coverage': 100.0,
                'status': True,
                'citations': ['citation'],
                'duplicates': ['duplicate'],
                'forbiddens': ['forbid'],
                'dtd_errors': ['dtd_errors'],
                'units': {
                    'Folder Name': True,
                    'MyCapytain': True
                },
                'logs': [
                    ">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml",
                    ">>>>> MyCapytain passed",
                    ">>>>> Folder Name passed"
                ],
                'language': 'grc'
            })
            self.assertEqual(logs.status, True)
            self.assertEqual(logs, self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"])

    @mock.patch("HookTest.test.time.strftime", return_value="Time")
    def test_unit_text_verbose(self, timed):
        self.test.verbose = True
        test = mock.MagicMock()
        test.return_value = [
            ("MyCapytain", True, []),
            ("Folder Name", False, ["It should be in a subfolder"])
        ]
        INVObject = mock.Mock(
            test=test, forbiddens=['forbid'], duplicates=['duplicate'], citation=['citation'], lang="grc",
            dtd_errors=['dtd_errors']
        )
        ctsunit = mock.Mock(
            return_value=INVObject
        )
        with mock.patch("HookTest.test.HookTest.capitains_units.cts.CTSText_TestUnit", ctsunit):
            logs, filepath, additional = self.test.unit("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml")
            ctsunit.assert_called_with("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml", countwords=False, timeout=30)
            self.assertIn(">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml", logs.logs)
            self.assertIn(">>>>> MyCapytain passed", logs.logs)
            self.assertIn(">>>>> Folder Name failed", logs.logs)
            self.assertIn("It should be in a subfolder", logs.logs)
            self.test.results[filepath] = logs

            self.assertEqual(self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"].dict, {
                'at': 'Time',
                'name': "/phi1294/phi002/phi1294.phi002.perseus-lat2.xml",
                'coverage': 50.0,
                'status': False,
                'citations': ['citation'],
                'duplicates': ['duplicate'],
                'forbiddens': ['forbid'],
                'dtd_errors': ['dtd_errors'],
                'units': {
                    'Folder Name': False,
                    'MyCapytain': True
                },
                'logs': [
                    ">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml",
                    ">>>>> MyCapytain passed",
                    ">>>>> Folder Name failed",
                    "It should be in a subfolder"
                ],
                'language': 'grc'
            })
            self.assertEqual(self.test.passing["phi1294.phi002.perseus-lat2.xml"], False)
            self.assertEqual(logs, self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"])

    @mock.patch("HookTest.test.Progress")
    @mock.patch("HookTest.test.git.repo.base.Remote")
    @mock.patch("HookTest.test.git.repo.base.Repo.clone_from")
    @mock.patch("HookTest.test.git.repo.base.Repo")
    def backup_clone(self, repo_mocked, clone_from_mocked, remote_mocked, progress_mocked):
        """ Check that the cloning is done correctly, ie. right branch, right path, etc. """
        # Finish mocking stuff
        pull = mock.MagicMock(return_value=True)
        remote_met = mock.MagicMock(return_value=remote_mocked)
        remote_mocked.pull = pull
        repo_mocked.remote = remote_met
        type(clone_from_mocked).return_value = repo_mocked

        # With a branch defined
        self.test.clone()
        progress_mocked.assert_called_with(parent=self.test)
        clone_from_mocked.assert_called_with(
            url="https://github.com/PerseusDL/tests.git",
            to_path="./1234",
            progress=self.test.progress,
            depth=10
        )
        self.assertEqual(self.test.branch, "refs/heads/dev")
        repo_mocked.remote.assert_called_with()
        remote_met.assert_called_with()
        pull.assert_called_with("refs/heads/dev", progress=self.test.progress)

        # With a branch as None
        self.test.branch = None
        self.test.clone()
        progress_mocked.assert_called_with(parent=self.test)
        clone_from_mocked.assert_called_with(
            url="https://github.com/PerseusDL/tests.git",
            to_path="./1234",
            progress=self.test.progress,
            depth=10
        )
        self.assertEqual(self.test.branch, "refs/heads/master")
        repo_mocked.remote.assert_called_with()
        remote_met.assert_called_with()
        pull.assert_called_with("refs/heads/master", progress=self.test.progress)

        # With a PR number as numeric string
        self.test.branch = "pull/5/head"
        self.test.clone()
        progress_mocked.assert_called_with(parent=self.test)
        clone_from_mocked.assert_called_with(
            url="https://github.com/PerseusDL/tests.git",
            to_path="./1234",
            progress=self.test.progress,
            depth=10
        )
        self.assertEqual(self.test.branch, "pull/5/head")
        repo_mocked.remote.assert_called_with()
        remote_met.assert_called_with()
        pull.assert_called_with("refs/pull/5/head", progress=self.test.progress)

    @mock.patch("HookTest.test.shutil.rmtree", create=True)
    def test_clean(self, mocked):
        """ Test remove is called """
        self.test.clean()
        mocked.assert_called_with("./1234", ignore_errors=True)

    def test_find(self):
        reading, metadata = (HookTest.test.Test("./tests/repo1")).find()
        self.assertEqual(len(metadata), 2, "It should find two __cts__ in repo1")
        self.assertEqual(len(reading), 3, "It should find three texts in repo1")  # eng far ger

    def test_cover(self):
        """ Test covering dict generation """
        test = {
            "One test": True,
            "Two test": False
        }
        test2 = {
            "One test": True,
            "Two test": True
        }
        test3 = {
            "One test": False,
            "Two test": False
        }
        with mock.patch("HookTest.test.time.strftime", return_value="Time") as time:
            self.assertEqual(
                self.test.cover("test1", test).dict,
                {
                    "units": {
                        "One test": True,
                        "Two test": False
                    },
                    "logs": [],
                    "name": "test1",
                    "coverage": 50.0,
                    "status": False,
                    "at": "Time"
                }
            )
            self.assertEqual(
                self.test.cover("test2", test2).dict,
                {
                    "units": {
                        "One test": True,
                        "Two test": True
                    },
                    "logs": [],
                    "name": "test2",
                    "coverage": 100.0,
                    "status": True,
                    "at": "Time"
                }
            )
            self.assertEqual(
                self.test.cover("test3", test3).dict,
                {
                    "units": {
                        "One test": False,
                        "Two test": False
                    },
                    "logs": [],
                    "name": "test3",
                    "coverage": 0.0,
                    "status": False,
                    "at": "Time"
                }
            )

    @mock.patch('HookTest.test.sys.stdout', create=True)
    def test_log_travis_pass(self, sysmocked):
        """ Testing a unit that passes prints . in stdout and then flush it """
        process = HookTest.test.Test("./tests/repo1", console="table")
        logs_dict = unitlog_dict()

        process.log(logs_dict["001"])
        sysmocked.write.assert_called_with(".")
        sysmocked.flush.assert_called_with()

    @mock.patch('HookTest.test.sys.stdout', create=True)
    def test_log_travis_fail(self, sysmocked):
        """ Testing a unit that fails prints X in stdout and then flush it """
        process = HookTest.test.Test("./tests/repo1", console="table")
        logs_dict = unitlog_dict()

        process.log(logs_dict["002"])
        sysmocked.write.assert_called_with("X")
        sysmocked.flush.assert_called_with()

    @mock.patch("HookTest.test.PT")
    def test_middle_nottravis_not_called(self, PTMock):
        """ Ensure PrettyTable are not created when travis is False """
        process = HookTest.test.Test("./tests/repo1", travis=False, verbose=False)
        process.results = unitlog_dict()
        process.results["001"].units = {
            "Metadata": True,
            "Filename": True
        }
        process.results["002"].units = {
            "Metadata": True,
            "Filename": False
        }
        process.middle()
        process.middle()
        PTMock.assert_not_called()

    @mock.patch("HookTest.test.print", create=True)  # We patch and feed print to PrintMock
    @mock.patch("HookTest.test.PT", create=True)  #  We patch PrettyTable and feed it as PTMock
    def test_middle_travis(self, PTMock, printMock):
        """ Ensure PrettyTable are created when travis is True and verbose as well """

        # PTMock being a class (PrettyTable), on instantiation it returns a new object.
        # So when python executes PT(["Filename", "Failed Tests"]), we need to have access to
        # the instance this call would create
        # Hence creating a mock and feeding it as return_value of PTMock
        InstanceMock = mock.MagicMock(create=True)
        PTMock.return_value = InstanceMock

        # We create a process of Test and feed weird results
        process = HookTest.test.Test("./tests/repo1", console="table", verbose=True)
        process.results = unitlog_dict()
        process.results["001"].units = {
            "Metadata": True,
            "Filename": True
        }
        process.results["002"].units = {
            "Metadata": True,
            "Filename": False
        }

        # We run the method we want to verify
        process.middle()

        # We check each call that should be done
        PTMock.assert_called_with(["Filename", "Failed Tests"])
        InstanceMock.align.__setitem__.assert_called_with(("Filename", "Failed Tests"), "c")
        # assert_called_once_with checks both that there has been only one call on the function tested, and then checks
        # that the parameters are the same
        InstanceMock.add_row.assert_called_once_with(["002", "Filename failed"])

        printMock.assert_has_calls([
            mock.call('', flush=True),
            mock.call(InstanceMock, flush=True)
        ])
        self.assertEqual(process.m_files, 2)
        self.assertEqual(process.m_passing, 1)

    @mock.patch("HookTest.test.print", create=True)  # We patch and feed print to PrintMock
    def test_middle_travis_pass(self, printMock):
        """ Ensure PrettyTable are created when travis is True and verbose as well """
        # We create a process of Test and feed weird results
        process = HookTest.test.Test("./tests/repo1", console="table", verbose=True)
        process.results = unitlog_dict()
        process.results["001"].units = {
            "Metadata": True,
            "Filename": True
        }
        process.results["002"].units = {
            "Metadata": True,
            "Filename": True
        }
        process.results["002"].status = True

        process.middle()

        printMock.assert_has_calls([
            mock.call('', flush=True),
            mock.call('All Metadata Files Passed', flush=True)
        ])
        self.assertEqual(process.m_files, 2)
        self.assertEqual(process.m_passing, 2)

    @mock.patch("HookTest.test.print", create=True)  # We patch and feed print to PrintMock
    @mock.patch("HookTest.test.PT", create=True)  # We patch PrettyTable and feed it as PTMock
    def test_end_no_counts(self, PTMock, printMock):
        """ Ensure PrettyTable is correctly created when travis is True and verbose as well """

        self.createTestDir('./tests/repo1')
        # PTMock being a class (PrettyTable), on instantiation it returns a new object.
        # So when python executes PT(["Filename", "Failed Tests"]), we need to have access to
        # the instance this call would create
        # Hence creating a mock and feeding it as return_value of PTMock
        InstanceMock = mock.MagicMock(create=True)
        PTMock.return_value = InstanceMock

        # We create a process of Test and feed weird results
        process = HookTest.test.Test(self.TESTDIR, console="table", verbose=10)
        process.results = unitlog_dict()
        process.results["001"].units = {
            "Metadata": True,
            "Filename": True,
            'Passage level parsing': True
        }
        process.results["001"].additional['citations'] = [(0, 2, 'Book'), (1, 3, 'Chapter'), (2, 4, 'Section')]
        process.results["001"].additional['duplicates'] = []
        process.results["001"].additional['forbiddens'] = []
        process.results["001"].additional['dtd_errors'] = []
        process.results["002"].units = {
            "Metadata": True,
            "Filename": False,
            'Passage level parsing': False
        }
        process.results["002"].additional['citations'] = []
        process.results["002"].additional['duplicates'] = ['1.1', '1.2']
        process.results["002"].additional['forbiddens'] = ['1$1', '1-1']
        process.results["002"].additional['dtd_errors'] = ['error: value of attribute "cause" is invalid [In (L112 C52)]']
        # add a unit where all tests fail
        process.results['003'] = HookTest.test.UnitLog(
            directory=".",
            name='003',
            units={},
            coverage=0.0,
            status=False
        )
        process.results['003'].units = {
            "Metadata": False,
            "Filename": False,
            'Passage level parsing': False
        }
        process.results["003"].additional['citations'] = []
        process.results["003"].additional['words'] = 0
        process.results["003"].additional['duplicates'] = []
        process.results["003"].additional['forbiddens'] = []
        process.results["003"].additional['dtd_errors'] = []
        process.m_passing = 3
        process.m_files = 3

        # We run the method we want to verify
        process.end()

        # We check each call that should be done
        PTMock.assert_has_calls([mock.call(['Identifier', 'Nodes', 'Failed Tests']),
                                 mock.call().align.__setitem__(('Identifier', 'Nodes', 'Failed Tests'), 'c'),
                                 mock.call().add_row(['\x1b[37m001\x1b[0m', '2;3;4', '']),
                                 mock.call().add_row(['\x1b[35m002\x1b[0m', '', 'Passage level parsing']),
                                 mock.call().add_row(['\x1b[35m003\x1b[0m', '', 'All']),
                                 mock.call(['HookTestResults', '']),
                                 mock.call().align.__setitem__(('HookTestResults', ''), 'c'),
                                 mock.call().add_row(['Total Texts', 3]),
                                 mock.call().add_row(['Passing Texts', 1]),
                                 mock.call().add_row(['Metadata Files', 3]),
                                 mock.call().add_row(['Passing Metadata', 3]),
                                 mock.call().add_row(['Coverage', 50.0]),
                                 mock.call().add_row(['Total Citation Units', '9'])])

        duplicate_nodes = '\x1b[35mDuplicate nodes found:\n\x1b[0m\t\x1b[35m002\x1b[0m\t1.1, 1.2\n\n'
        forbidden_chars = '\x1b[35mForbidden characters found:\n\x1b[0m\t\x1b[35m002\x1b[0m\t1$1, 1-1\n\n'
        dtd_errors = '\x1b[35mDTD errors found:\n\x1b[0m\t\x1b[35m002\x1b[0m\terror: value of attribute "cause" is invalid [In (L112 C52)]\n\n'
        printMock.assert_has_calls([
            mock.call('', flush=True),
            mock.call(InstanceMock, flush=True),
            mock.call("{dupes}{forbs}{dtds}>>> End of the test !\n".format(dupes=duplicate_nodes,
                                                                           forbs=forbidden_chars,
                                                                           dtds=dtd_errors))
        ], any_order=True)

    @mock.patch("HookTest.test.print", create=True)  # We patch and feed print to PrintMock
    @mock.patch("HookTest.test.PT", create=True)  # We patch PrettyTable and feed it as PTMock
    def test_end_with_counts(self, PTMock, printMock):
        """ Ensure PrettyTable is correctly created when travis, verbose and countwords are True """

        self.createTestDir('./tests/repo1')
        # PTMock being a class (PrettyTable), on instantiation it returns a new object.
        # So when python executes PT(["Filename", "Failed Tests"]), we need to have access to
        # the instance this call would create
        # Hence creating a mock and feeding it as return_value of PTMock
        InstanceMock = mock.MagicMock(create=True)
        PTMock.return_value = InstanceMock

        # We create a process of Test and feed weird results
        process = HookTest.test.Test(self.TESTDIR, console="table", verbose=10, countwords=True)
        process.results = unitlog_dict()
        process.results["001"].units = {
            "Metadata": True,
            "Filename": True,
            'Passage level parsing': True
        }
        process.results["001"].additional['citations'] = [(0, 2, 'Book'), (1, 3, 'Chapter'), (2, 4, 'Section')]
        process.results["001"].additional['words'] = 100
        process.results["001"].additional['duplicates'] = []
        process.results["001"].additional['forbiddens'] = []
        process.results["001"].additional['dtd_errors'] = []
        process.results["001"].additional['language'] = 'UNK'
        process.results["002"].units = {
            "Metadata": True,
            "Filename": False,
            'Passage level parsing': False
        }
        process.results["002"].additional['citations'] = []
        process.results["002"].additional['words'] = 50
        process.results["002"].additional['duplicates'] = ['1.1', '1.2']
        process.results["002"].additional['forbiddens'] = ['1$1', '1-1']
        process.results["002"].additional['dtd_errors'] = ['error: value of attribute "cause" is invalid [In (L112 C52)]']
        process.results["002"].additional['language'] = 'UNK'
        # add a unit where all tests fail
        process.results['003'] = HookTest.test.UnitLog(
            directory=".",
            name='003',
            units={},
            coverage=0.0,
            status=False
        )
        process.results['003'].units = {
            "Metadata": False,
            "Filename": False,
            'Passage level parsing': False
        }
        process.results["003"].additional['citations'] = []
        process.results["003"].additional['words'] = 0
        process.results["003"].additional['duplicates'] = []
        process.results["003"].additional['forbiddens'] = []
        process.results["003"].additional['dtd_errors'] = []
        process.results["003"].additional['language'] = 'UNK'
        process.m_passing = 3
        process.m_files = 3

        # We run the method we want to verify
        process.end()

        # We check each call that should be done
        PTMock.assert_has_calls([mock.call(["Identifier", "Words", "Nodes", "Failed Tests"]),
                                 mock.call().align.__setitem__(("Identifier", "Words", "Nodes", "Failed Tests"), 'c'),
                                 mock.call().add_row(['\x1b[37m001\x1b[0m', '100', '2;3;4', '']),
                                 mock.call().add_row(['\x1b[35m002\x1b[0m', '50', '', 'Passage level parsing']),
                                 mock.call().add_row(['\x1b[35m003\x1b[0m', '0', '', 'All']),
                                 mock.call(['HookTestResults', '']),
                                 mock.call().align.__setitem__(('HookTestResults', ''), 'c'),
                                 mock.call().add_row(['Total Texts', 3]),
                                 mock.call().add_row(['Passing Texts', 1]),
                                 mock.call().add_row(['Metadata Files', 3]),
                                 mock.call().add_row(['Passing Metadata', 3]),
                                 mock.call().add_row(['Coverage', 50.0]),
                                 mock.call().add_row(['Total Citation Units', '9']),
                                 mock.call().add_row(['Total Words', '150'])])

        duplicate_nodes = '\x1b[35mDuplicate nodes found:\n\x1b[0m\t\x1b[35m002\x1b[0m\t1.1, 1.2\n\n'
        forbidden_chars = '\x1b[35mForbidden characters found:\n\x1b[0m\t\x1b[35m002\x1b[0m\t1$1, 1-1\n\n'
        dtd_errors = '\x1b[35mDTD errors found:\n\x1b[0m\t\x1b[35m002\x1b[0m\terror: value of attribute "cause" is invalid [In (L112 C52)]\n\n'
        printMock.assert_has_calls([
            mock.call('', flush=True),
            mock.call(InstanceMock, flush=True),
            mock.call("{dupes}{forbs}{dtds}>>> End of the test !\n".format(dupes=duplicate_nodes,
                                                                           forbs=forbidden_chars,
                                                                           dtds=dtd_errors))
        ], any_order=True)

    @mock.patch("HookTest.test.print", create=True)  # We patch and feed print to PrintMock
    @mock.patch("HookTest.test.PT", create=True)  # We patch PrettyTable and feed it as PTMock
    def test_end_not_verbose(self, PTMock, printMock):
        """ Ensure PrettyTable is correctly created when travis is True and verbose as well """

        self.createTestDir('./tests/repo1')
        # PTMock being a class (PrettyTable), on instantiation it returns a new object.
        # So when python executes PT(["Filename", "Failed Tests"]), we need to have access to
        # the instance this call would create
        # Hence creating a mock and feeding it as return_value of PTMock
        InstanceMock = mock.MagicMock(create=True)
        PTMock.return_value = InstanceMock

        # We create a process of Test and feed weird results
        process = HookTest.test.Test(self.TESTDIR, console="table", verbose=0)
        process.results = unitlog_dict()
        process.results["001"].units = {
            "Metadata": True,
            "Filename": True,
            'Passage level parsing': True
        }
        process.results["001"].additional['citations'] = [(0, 2, 'Book'), (1, 3, 'Chapter'), (2, 4, 'Section')]
        process.results["001"].additional['duplicates'] = []
        process.results["001"].additional['forbiddens'] = []
        process.results["001"].additional['dtd_errors'] = []
        process.results["002"].units = {
            "Metadata": True,
            "Filename": False,
            'Passage level parsing': False
        }
        process.results["002"].additional['citations'] = []
        process.results["002"].additional['duplicates'] = ['1.1', '1.2']
        process.results["002"].additional['forbiddens'] = ['1$1', '1-1']
        process.results["002"].additional['dtd_errors'] = ['error: value of attribute "cause" is invalid [In (L112 C52)]']
        # add a unit where all tests fail
        process.results['003'] = HookTest.test.UnitLog(
            directory=".",
            name='003',
            units={},
            coverage=0.0,
            status=False
        )
        process.results['003'].units = {
            "Metadata": False,
            "Filename": False,
            'Passage level parsing': False
        }
        process.results["003"].additional['citations'] = []
        process.results["003"].additional['words'] = 0
        process.results["003"].additional['duplicates'] = []
        process.results["003"].additional['forbiddens'] = []
        process.results["003"].additional['dtd_errors'] = []
        process.m_passing = 3
        process.m_files = 3

        # We run the method we want to verify
        process.end()
        
        # We check each call that should be done
        PTMock.assert_has_calls([mock.call(['Identifier', 'Nodes', 'Failed Tests']),
                                 mock.call().align.__setitem__(('Identifier', 'Nodes', 'Failed Tests'), 'c'),
                                 #mock.call().add_row(['\x1b[37m001\x1b[0m', '2;3;4', '']),
                                 mock.call().add_row(['\x1b[35m002\x1b[0m', '', 'Passage level parsing']),
                                 mock.call().add_row(['\x1b[35m003\x1b[0m', '', 'All']),
                                 mock.call(['HookTestResults', '']),
                                 mock.call().align.__setitem__(('HookTestResults', ''), 'c'),
                                 mock.call().add_row(['Total Texts', 3]),
                                 mock.call().add_row(['Passing Texts', 1]),
                                 mock.call().add_row(['Metadata Files', 3]),
                                 mock.call().add_row(['Passing Metadata', 3]),
                                 mock.call().add_row(['Coverage', 50.0]),
                                 mock.call().add_row(['Total Citation Units', '9'])])

        duplicate_nodes = ''
        forbidden_chars = ''
        dtd_errors = ''
        printMock.assert_has_calls([
            mock.call('', flush=True),
            mock.call(InstanceMock, flush=True),
            mock.call("{dupes}{forbs}{dtds}>>> End of the test !\n".format(dupes=duplicate_nodes,
                                                                           forbs=forbidden_chars,
                                                                           dtds=dtd_errors))
        ], any_order=True)

    def test_manifest_build(self):
        """ Ensure that the manifest is created correctly,
            adding only the files that have a passing group-level and work-level __cts__.xml file
            and a passing CTS text file
        """

        self.createTestDir('./tests/repo1')

        process = HookTest.test.Test(self.TESTDIR, console="table", verbose=10, countwords=True, build_manifest=True)
        process.results = unitlog_dict()
        process.results['001'].name = 'test/test/test'
        process.results["002"].name = 'test/test/__cts__.xml'
        process.results['002'].coverage = 100.0
        process.results['003'] = HookTest.test.UnitLog(
            directory=".",
            name='test/__cts__.xml',
            units={},
            coverage=100.0,
            status=False
        )
        # this statement is necessary because for some reason the assignment of the .name attr above leaves out the .
        process.results['003'].name = 'test/__cts__.xml'
        # produce 3 new constellations of files that will fail at some point
        for n in (4, 7, 10):
            process.results['00{}'.format(n)] = HookTest.test.UnitLog(
                directory=".",
                name='test{0}/test{0}/test{0}'.format(n),
                units={},
                coverage=100.0,
                status=False
            )
            process.results['00{}'.format(n + 1)] = HookTest.test.UnitLog(
                directory=".",
                name='test{0}/test{0}/__cts__.xml'.format(n),
                units={},
                coverage=100.0,
                status=False
            )
            process.results['00{}'.format(n + 1)].name = 'test{0}/test{0}/__cts__.xml'.format(n)
            process.results['00{}'.format(n + 2)] = HookTest.test.UnitLog(
                directory=".",
                name='test{0}/__cts__.xml'.format(n),
                units={},
                coverage=100.0,
                status=False
            )
            process.results['00{}'.format(n + 2)].name = 'test{0}/__cts__.xml'.format(n)
        # case where the text file fails
        process.results['004'].coverage = 50.0
        # case where the work-level __cts__.xml file fails
        process.results['008'].coverage = 50.0
        # case where the group-level __cts__.xml file fails
        process.results['0012'].coverage = 50.0
        # We run the method we want to verify
        self.assertEqual(process.create_manifest(), ['test/__cts__.xml', 'test/test/__cts__.xml', 'test/test/test'])

    @mock.patch('HookTest.test.requests.post', create=True)
    def test_travis_to_hook_push(self, post):
        """ Test printing function """
        test = HookTest.test.Test(
            path="weDoNotCare",
            from_travis_to_hook="https://ci.perseids.org"
        )
        test.results = unitlog_dict()

        with mock.patch.dict(
                'HookTest.test.os.environ',
                {
                    "TRAVIS_EVENT_TYPE": "push",
                    "TRAVIS_BUILD_ID": "asdfgh",
                    "TRAVIS_REPO_SLUG": "ponteineptique/canonical-latinLit",
                    "TRAVIS_BUILD_NUMBER": "27",
                    "TRAVIS_COMMIT": "qwertyu",
                    "TRAVIS_BRANCH": "issue-151"
                }):
            test.send_to_hook_from_travis(
                texts_total=577, texts_passing=544,
                metadata_total=800, metadata_passing=678,
                coverage=90.45, nodes_count=789456,
                words_dict={
                    "eng": 745321,
                    "lat": 123456
                }
            )
        name, args, kwargs = post.mock_calls[0]
        self.assertEqual(
            args, ("https://ci.perseids.org", ),
            "URI should be the one set up"
        )
        self.assertEqual(
            json.loads(kwargs["data"].decode()),
            {"build_id": "27", "build_uri": "https://travis-ci.org/ponteineptique/canonical-latinLit/builds/asdfgh", "commit_sha": "qwertyu",
             "coverage": 90.45, "event_type": "push", "metadata_passing": 678, "metadata_total": 800,
             "nodes_count": 789456, "source": "issue-151", "texts_passing": 544, "texts_total": 577,
             "units": {"001": True, "002": False}, "words_count": {"eng": 745321, "lat": 123456}},
            "Data should cover everything"
        )
        self.assertEqual(
            kwargs["headers"],
            {
                'Content-Type': 'application/json',
                'HookTest-Secure-X': '988bbbf8f3ac4e89298e858451f8512eb049ac39'
            },
            "Headers should say json and have a good secure"
        )
        self.assertEqual(
            json.loads(kwargs["data"].decode()),
            {"build_id": "27", "build_uri": "https://travis-ci.org/ponteineptique/canonical-latinLit/builds/asdfgh", "commit_sha": "qwertyu",
             "coverage": 90.45, "event_type": "push", "metadata_passing": 678, "metadata_total": 800,
             "nodes_count": 789456, "source": "issue-151", "texts_passing": 544, "texts_total": 577,
             "units": {"001": True, "002": False}, "words_count": {"eng": 745321, "lat": 123456}},
            "Data should cover everything"
        )

    @mock.patch('HookTest.test.requests.post', create=True)
    def test_travis_to_hook_pull_request(self, post):
        """ Test printing function """
        test = HookTest.test.Test(
            path="weDoNotCare",
            from_travis_to_hook="https://ci.perseids.org"
        )
        test.results = unitlog_dict()
        with mock.patch.dict(
                'HookTest.test.os.environ',
                {
                    "TRAVIS_EVENT_TYPE": "pull_request",
                    "TRAVIS_BUILD_ID": "asdfgh",
                    "TRAVIS_REPO_SLUG": "ponteineptique/canonical-latinLit",
                    "TRAVIS_BUILD_NUMBER": "27",
                    "TRAVIS_COMMIT": "qwertyu",
                    "TRAVIS_PULL_REQUEST": "151"
                }):
            test.send_to_hook_from_travis(
                texts_total=577, texts_passing=544,
                metadata_total=800, metadata_passing=678,
                coverage=90.45, nodes_count=789456,
                words_dict={
                    "eng": 745321,
                    "lat": 123456
                }
            )

        name, args, kwargs = post.mock_calls[0]
        self.assertEqual(
            args, ("https://ci.perseids.org", ),
            "URI should be the one set up"
        )
        self.assertEqual(
            json.loads(kwargs["data"].decode()),
            {"build_id": "27", "build_uri": "https://travis-ci.org/ponteineptique/canonical-latinLit/builds/asdfgh", "commit_sha": "qwertyu",
             "coverage": 90.45, "event_type": "pull_request", "metadata_passing": 678, "metadata_total": 800,
             "nodes_count": 789456, "source": "151", "texts_passing": 544, "texts_total": 577,
             "units": {"001": True, "002": False}, "words_count": {"eng": 745321, "lat": 123456}},
            "Data should cover everything"
        )
        self.assertEqual(
            kwargs["headers"],
            {
                'Content-Type': 'application/json',
                'HookTest-Secure-X': 'fabd496ac0c316032487b67079d6fc9731e8f7f7'
            },
            "Headers should say json and have a good secure"
        )

class TestProgress(unittest.TestCase):
    """ Test Github.Progress own implementation """

    def test_json(self):
        """ Test Own Progress function """
        P = HookTest.test.Progress()
        self.assertEqual(len(P.json), 3)

        P.start = ["This is a start", "AHAH"]
        P.end = ["This is an end"]
        P.current = 5
        P.maximum = 10
        P.download = 20

        self.assertEqual(P.json, [
            "This is a start\nAHAH",
            "Downloaded 5/10 (20)",
            "This is an end"
        ])

    def test_update(self):
        P = HookTest.test.Progress()

        # Testing first logs
        P.update(1, 2, max_count=3, message="Starting Download")
        self.assertEqual(P.start, ["Cloning repository", "Starting Download"])

        # Testing when there is a speed
        P.update(1, 2, max_count=3, message='55 kb/s')
        self.assertEqual(P.progress, True)
        self.assertEqual(P.download, '55 kb/s')

        # Testing end logs
        P.update(1, 2, max_count=3, message="Ending Download")
        self.assertEqual(P.progress, False)
        self.assertEqual(P.end, ["Ending Download"])


class TestUnitLogs(unittest.TestCase):
    def test_init(self):
        pass

    def test_dict(self):
        pass

    def test_directory_replacer(self):
        """ Test to make sure the correct value is returned by directory_replacer function
        """
        #test in current directory
        log = HookTest.test.UnitLog(
            directory=".",
            name='tlg0000.tlg000.tlg00.xml',
            units={},
            coverage=100.0,
            status=False
        )
        self.assertEqual(log.name, 'tlg0000.tlg000.tlg00.xml')

        #test in different directory
        log = HookTest.test.UnitLog(
            directory="test/",
            name='test/tlg0000.tlg000.tlg00.xml',
            units={},
            coverage=100.0,
            status=False
        )
        self.assertEqual(log.name, 'tlg0000.tlg000.tlg00.xml')

        # test with repository
        log = HookTest.test.UnitLog(
            directory="test/First1K",
            repository="First1K",
            name='test/First1K/tlg0000.tlg000.tlg00.xml',
            units={},
            coverage=100.0,
            status=False
        )
        self.assertEqual(log.name, 'First1K/tlg0000.tlg000.tlg00.xml')

        # test with repository and current directory
        log = HookTest.test.UnitLog(
            directory="./First1K",
            repository="First1K",
            name='./First1K/tlg0000.tlg000.tlg00.xml',
            units={},
            coverage=100.0,
            status=False
        )
        self.assertEqual(log.name, 'First1K/tlg0000.tlg000.tlg00.xml')
