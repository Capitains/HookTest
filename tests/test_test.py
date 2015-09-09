import unittest
import HookTest.test
import HookTest.units
import mock
import json
import concurrent.futures


class TestTest(unittest.TestCase):
    def setUp(self):
        self.test = HookTest.test.Test(
            "./",
            repository="PerseusDL/tests",
            branch="dev",
            uuid="1234",
            ping="http://services.perseids.org/Hook",
            secret="PerseusDL"
        )
        self.test_print = HookTest.test.Test(
            "./",
            repository="PerseusDL",
            branch="master",
            uuid="1234",
            secret="PerseusDL"
        )

    def test_dump(self):
        self.assertEqual(Test.dump(), "{'Test':")

    @mock.patch('HookTest.test.print', create=True)
    def test_write_with_print(self, mocked):
        """ Test writing function """
        # Test normal use
        # When print is not set to True
        self.test_print.write("This is a log")
        mocked.assert_not_called()

        # When it is
        self.test_print.print = True
        self.test_print.download = {"test": True}
        self.test_print.write(None)
        mocked.assert_called_with({"test": True}, flush=True)

        self.test_print.write("This is a log")
        mocked.assert_called_with("This is a log", flush=True)

        self.test.print = True
        self.test.ping = None
        self.test.write("./1234/file1.xml is good")  # Check its uuid is replaced
        mocked.assert_called_with("PerseusDL/tests/file1.xml is good", flush=True)

        self.test.uuid = None
        self.test.write("./1234/file2.xml is good")  # Check its uuid is replaced
        mocked.assert_called_with("./1234/file2.xml is good", flush=True)

        self.test.repository = None
        self.test.write("./file3.xml is good")  # Check its uuid is replaced
        mocked.assert_called_with("file3.xml is good", flush=True)

    @mock.patch('HookTest.test.sending', create=True)
    def test_write_with_request(self, mocked):
        """ Test writing function when sending request param """
        self.test.print = True
        self.test.printing = mocked
        self.test.logs = ["1"] * 48  # Up to 49 it should send nothing
        self.test.write("1")
        mocked.assert_not_called()

        self.test.write("1")
        mocked.assert_called_with(["1"] * 50)

        self.test.logs += ["2"] * 48
        self.test.write("2")
        mocked.assert_not_called()
        self.test.write("2")
        mocked.assert_called_with(["2"] * 50)

        self.test.logs += ["3"] * 480
        self.test.write("3")
        mocked.assert_called_with(["3"] * 481)
        self.test.write("4")
        mocked.assert_not_called()

    @mock.patch('HookTest.test.sending', create=True)
    def test_flush(self, mocked):
        """ Test the flush method, which sends the remaining logs to be treated
        """
        self.test.print = True
        self.test.printing = mocked

        # Empty flushing
        self.test.flush()
        mocked.assert_not_called()

        # Test with normal logs
        self.test.logs = ["1"] * 49
        self.test.write("1")
        mocked.assert_called_with(50 * ["1"])

        # And now increment and flush
        self.test.logs += ["2"] * 25
        self.test.flush()
        mocked.assert_called_with(25 * ["2"])

    @mock.patch('HookTest.test.requests.post', create=True)
    def test_printing_over_http(self, mocked):
        """ Test printing function """
        self.test.printing(["5"] * 50)
        mocked.assert_called_with(
            "http://services.perseids.org/Hook",
            data=bytes(json.dumps({"log": ["5"] * 50}), "utf-8"),
            headers={
                "HookTest-Secure-X": "76f6c41bc0f4df0eddae51f2739f0bf244a83a53",
                'HookTest-UUID': '1234'
            }
        )

        data = {"this": "is a dict"}
        self.test.printing(data)
        mocked.assert_called_with(
            "http://services.perseids.org/Hook",
            data=bytes(json.dumps(data), "utf-8"),
            headers={
                "HookTest-Secure-X": "1af4394c8b251da317b461b6051eeebd125b837c",
                'HookTest-UUID': '1234'
            }
        )

    def test_send_report(self):
        """ Test sending report """
        #  Check it does nothing if no ping
        self.test.ping = None
        printing = self.test.printing
        self.test.printing = lambda x: True
        self.assertIsNone(self.test.send_report(None))

        #  Check it does when there is a ping
        self.test.ping = "http://services.perseids.org/Hook"
        self.assertEqual(self.test.send_report(None), True)
        self.test.printing = printing

    def test_successes(self):
        """ Test successes property
        """
        self.test.passing = {"1": True, "2": True, "3": False}
        self.assertEqual(self.test.successes, 2)
        self.test.passing = {"1": True, "2": False, "3": False}
        self.assertEqual(self.test.successes, 1)
        self.test.passing = {}
        self.assertEqual(self.test.successes, 0)

    def test_finish(self):
        """ Check that finishes return a consistent status
        """
        self.test.passing = {"001": True}
        self.test.text_files = [1]
        self.test.cts_files = [1]

        self.assertEqual(self.test.status, "error")  # 1/2 passing
        self.test.passing["002"] = False
        self.assertEqual(self.test.status, "failure")  # 1/2 successes
        self.test.passing["002"] = True
        self.assertEqual(self.test.status, "success")  # 2/2 successes

    def test_json(self):
        """ Check that json return is stable
        """
        report = json.dumps({
            "status": False,
            "units": {"001": {"coverage": 0.5}, "002": {"coverage": 0.5}},
            "coverage": 0.5
        })
        self.test.passing = {"001": True, "002": False}
        self.test.results = {"001": {"coverage": 0.5}, "002": {"coverage": 0.5}}
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

    def test_unit_inv_verbose(self):
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
            logs = self.test.unit("__cts__.xml")
            self.assertIn(">>>> Testing __cts__.xml", logs)
            self.assertIn(">>>>> MyCapytain passed", logs)
            self.assertIn(">>>>> Folder Name failed", logs)
            self.assertIn("It should be in a subfolder", logs)
            self.assertIn("urn:cts:latinLit:phi1294.phi002.perseus-lat2", self.test.inventory)

            self.assertEqual(self.test.results["__cts__.xml"], {
                'coverage': 50.0,
                'status': False,
                'units': {
                    'Folder Name': False,
                    'MyCapytain': True
                }
            })
            self.assertEqual(self.test.passing["__cts__.xml"], False)

    def test_unit_inv_non_verbose(self):
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
            logs = self.test.unit("/phi1294/phi002/__cts__.xml")
            self.assertIn(">>>> Testing /phi1294/phi002/__cts__.xml", logs)
            self.assertIn(">>>>> MyCapytain passed", logs)
            self.assertIn(">>>>> Folder Name passed", logs)
            self.assertIn("urn:cts:latinLit:phi1294.phi002.perseus-lat2", self.test.inventory)

            self.assertEqual(self.test.results["/phi1294/phi002/__cts__.xml"], {
                'coverage': 100.0,
                'status': True,
                'units': {
                    'Folder Name': True,
                    'MyCapytain': True
                }
            })

            self.assertEqual(self.test.passing[".phi1294.phi002.__cts__.xml"], True)

    def test_unit_text_mute(self):
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
            logs = self.test.unit("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml")
            self.assertIn(">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml", logs)
            self.assertIn(">>>>> MyCapytain passed", logs)
            self.assertIn(">>>>> Folder Name passed", logs)

            self.assertEqual(self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"], {
                'coverage': 100.0,
                'status': True,
                'units': {
                    'Folder Name': True,
                    'MyCapytain': True
                }
            })
            self.assertEqual(self.test.passing["phi1294.phi002.perseus-lat2.xml"], True)

    def test_unit_text_verbose(self):
        self.test.verbose = True
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
            logs = self.test.unit("/phi1294/phi002/phi1294.phi002.perseus-lat2.xml")
            self.assertIn(">>>> Testing /phi1294/phi002/phi1294.phi002.perseus-lat2.xml", logs)
            self.assertIn(">>>>> MyCapytain passed", logs)
            self.assertIn(">>>>> Folder Name passed", logs)
            self.assertIn("It should be in a subfolder", logs)

            self.assertEqual(self.test.results["/phi1294/phi002/phi1294.phi002.perseus-lat2.xml"], {
                'coverage': 100.0,
                'status': True,
                'units': {
                    'Folder Name': True,
                    'MyCapytain': True
                }
            })
            self.assertEqual(self.test.passing["phi1294.phi002.perseus-lat2.xml"], True)

    @mock.patch(
        "HookTest.test.concurrent.futures.ThreadPoolExecutor",
        spec=concurrent.futures.ThreadPoolExecutor,
        create=True
    )
    @mock.patch(
        "HookTest.test.concurrent.futures.as_completed",
        spec=concurrent.futures.as_completed,
        create=True
    )
    def test_run(self, on_complete, thread):
        """ Test that run make every call in the right order """

        # Mocking methods
        send_report = mock.MagicMock()
        flush = mock.PropertyMock()
        write = mock.MagicMock()
        self.test.uuid = "tests"
        self.test.send_report = send_report
        self.test.flush = flush
        self.test.write = write
        self.test.results = {"001": {"coverage": 100.00}, "002": {"coverage": 50.00}}

        #mocking concurrent
        result = mock.MagicMock(return_value=["1", "2", "3"])
        future = mock.MagicMock()
        future.result = result
        on_complete.return_value = [future]

        # Running
        thread().__enter__().submit.return_value = "This is a call"
        self.test.run()
        thread.assert_called_with(max_workers=1)
        thread().__enter__().submit.assert_any_call(
            self.test.unit,
            './tests/data/hafez/__cts__.xml'
        )
        thread().__enter__().submit.assert_any_call(
            self.test.unit,
            './tests/data/hafez/divan/__cts__.xml'
        )
        thread().__enter__().submit.assert_any_call(
            self.test.unit,
            './tests/data/hafez/divan/hafez.divan.perseus-ger1.xml'
        )
        thread().__enter__().submit.assert_any_call(
            self.test.unit,
            './tests/data/hafez/divan/hafez.divan.perseus-far1.xml'
        )
        thread().__enter__().submit.assert_any_call(
            self.test.unit,
            './tests/data/hafez/divan/hafez.divan.perseus-eng1.xml'
        )

        on_complete.assert_called_with({"This is a call": './tests/data/hafez/divan/hafez.divan.perseus-ger1.xml'})
        result.assert_called_with()

        write.assert_has_calls(
            [
                mock.call(">>> Starting tests !"),
                mock.call("files=5"),
                mock.call("1"),
                mock.call("2"),
                mock.call("3"),
                mock.call("1"),
                mock.call("2"),
                mock.call("3"),
                mock.call(">>> Finished tests !"),
                mock.call('[error] 0 over 0 texts have fully passed the tests')
            ]
        )

        flush.assert_called_with()
        send_report.assert_called_with()

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
            progress=self.test.progress
        )
        self.assertEqual(self.test.branch, "dev")
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
            progress=self.test.progress
        )
        self.assertEqual(self.test.branch, "master")
        repo_mocked.remote.assert_called_with()
        remote_met.assert_called_with()
        pull.assert_called_with("refs/heads/master", progress=self.test.progress)

        # With a PR number as int
        self.test.branch = 4
        self.test.clone()
        progress_mocked.assert_called_with(parent=self.test)
        clone_from_mocked.assert_called_with(
            url="https://github.com/PerseusDL/tests.git",
            to_path="./1234",
            progress=self.test.progress
        )
        self.assertEqual(self.test.branch, 4)
        repo_mocked.remote.assert_called_with()
        remote_met.assert_called_with()
        pull.assert_called_with("refs/pull/4/head:refs/pull/origin/4", progress=self.test.progress)

        # With a PR number as numeric string
        self.test.branch = "5"
        self.test.clone()
        progress_mocked.assert_called_with(parent=self.test)
        clone_from_mocked.assert_called_with(
            url="https://github.com/PerseusDL/tests.git",
            to_path="./1234",
            progress=self.test.progress
        )
        self.assertEqual(self.test.branch, "5")
        repo_mocked.remote.assert_called_with()
        remote_met.assert_called_with()
        pull.assert_called_with("refs/pull/5/head:refs/pull/origin/5", progress=self.test.progress)

    @mock.patch("HookTest.test.shutil.rmtree", create=True)
    def test_clean(self, mocked):
        """ Test remove is called """
        self.test.clean()
        mocked.assert_called_with("./1234", ignore_errors=True)

    def test_find(self):
        reading, metadata = HookTest.test.Test.find("./tests")
        self.assertEqual(len(metadata), 2)
        self.assertEqual(len(reading), 3) # eng far ger

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
        self.assertEqual(
            HookTest.test.Test.cover(test),
            {
                "units": {
                    "One test": True,
                    "Two test": False
                },
                "coverage": 50.0,
                "status": False
            }
        )
        self.assertEqual(
            HookTest.test.Test.cover(test2),
            {
                "units": {
                    "One test": True,
                    "Two test": True
                },
                "coverage": 100.0,
                "status": True
            }
        )
        self.assertEqual(
            HookTest.test.Test.cover(test3),
            {
                "units": {
                    "One test": False,
                    "Two test": False
                },
                "coverage": 0.0,
                "status": False
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