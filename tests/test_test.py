import unittest
import HookTest.test
import mock
import json


class TestTest(unittest.TestCase):
    def setUp(self):
        self.test = HookTest.test.Test(
            "./",
            repository="PerseusDL/tests",
            branch="master",
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
        self.test.passing = {"001" : True}
        self.test.files = [1]
        self.test.cts_files = [1]

        self.assertEqual(self.test.finish(), "error")  # 1/2 passing
        self.test.passing["002"] = False
        self.assertEqual(self.test.finish(), "failure")  # 1/2 successes
        self.test.passing["002"] = True
        self.assertEqual(self.test.finish(), "success")  # 2/2 successes

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

    def test_unit(self):
        pass

    def test_run(self):
        pass

    def test_clone(self):
        pass

    def test_clean(self):
        pass

    def test_files(self):
        reading, metadata = HookTest.test.Test.files("./tests")
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