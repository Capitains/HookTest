import unittest
import HookTest.test
import HookTest.units
import mock
import json
from multiprocessing.pool import Pool
from collections import OrderedDict


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
        self.test_print.console = True
        self.test_print.log("This is a log")
        mocked.assert_called_with("This is a log", flush=True)

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
        self.test_print.console = True
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
        self.test_print.console = True
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
            ">>> End of the test !\n>>> [failed] 5 over 7 texts have fully passed the tests", flush=True
        )

    @mock.patch('HookTest.test.print', create=True)
    def test_download(self, printed):
        self.test_print.download()
        self.assertEqual(len(printed.mock_calls), 0, msg="When print is not set, nothing is shown")

        self.test.download()
        self.assertEqual(len(printed.mock_calls), 0, msg="When print is not set, nothing is shown [Neither with Ping]")

        self.test_print.console = True
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
        with mock.patch("HookTest.test.HookTest.units.INVUnit", invunit):
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
        with mock.patch("HookTest.test.HookTest.units.INVUnit", invunit):
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
        test = mock.MagicMock()
        test.return_value = [
            ("MyCapytain", True, []),
            ("Folder Name", True, ["It should be in a subfolder"])
        ]
        INVObject = mock.Mock(
            test=test
        )
        ctsunit = mock.Mock(
            return_value=INVObject
        )
        with mock.patch("HookTest.test.HookTest.units.CTSUnit", ctsunit):
            logs, filepath, additional = self.test.unit("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml")
            self.assertIn(">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml", logs.logs)
            self.assertIn(">>>>> MyCapytain passed", logs.logs)
            self.assertIn(">>>>> Folder Name passed", logs.logs)
            self.test.results[filepath] = logs

            self.assertEqual(self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"].dict, {
                'name': '/phi1294/phi002/phi1294.phi002.perseus-lat2.xml',
                'at': 'Time',
                'coverage': 100.0,
                'status': True,
                'units': {
                    'Folder Name': True,
                    'MyCapytain': True
                },
                'logs': [
                    ">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml",
                    ">>>>> MyCapytain passed",
                    ">>>>> Folder Name passed"
                ]
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
            test=test
        )
        ctsunit = mock.Mock(
            return_value=INVObject
        )
        with mock.patch("HookTest.test.HookTest.units.CTSUnit", ctsunit):
            logs, filepath, additional = self.test.unit("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml")
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
                'units': {
                    'Folder Name': False,
                    'MyCapytain': True
                },
                'logs': [
                    ">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml",
                    ">>>>> MyCapytain passed",
                    ">>>>> Folder Name failed",
                    "It should be in a subfolder"
                ]
            })
            self.assertEqual(self.test.passing["phi1294.phi002.perseus-lat2.xml"], False)
            self.assertEqual(logs, self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"])

    @mock.patch("HookTest.test.Progress")
    @mock.patch("HookTest.test.git.repo.base.Remote")
    @mock.patch("HookTest.test.git.repo.base.Repo.clone_from")
    @mock.patch("HookTest.test.git.repo.base.Repo")
    def test_clone(self, repo_mocked, clone_from_mocked, remote_mocked, progress_mocked):
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
