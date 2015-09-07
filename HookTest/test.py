# -*- coding: utf-8 -*-

import os
import glob
import statistics

from collections import defaultdict
import concurrent.futures
import json
import git
import shutil
import requests
import hashlib
import hmac

import HookTest.units


class Test(object):
    """ Create a Test object

    :param path: Path where the test should happen
    :type path: str
    :param uuid: Identifier for the test
    :type uuid: str
    :param repository: URI of the repository
    :type repository: str
    :param branch: Identifier of the branch
    :type branch: str
    :param workers: Number of simultaneous workers to be used
    :type workers: str
    :param scheme: Name of the scheme
    :type scheme: str
    :param verbose: Log also rng and unit logs details
    :type verbose: bool
    """
    SCHEMES = {
        "tei": "tei.rng",
        "epidoc": "epidoc.rng"
    }

    def __init__(self, path,
         repository=None, branch=None, uuid=None, workers=1, scheme="tei",
         verbose=False, ping=False, secret=""
    ):
        """ Create a Test object

        :param path: Path where the test should happen
        :type path: str
        :param uuid: Identifier for the test
        :type uuid: str
        :param repository: URI of the repository
        :type repository: str
        :param branch: Identifier of the branch
        :type branch: str
        :param workers: Number of simultaneous workers to be used
        :type workers: str
        :param scheme: Name of the scheme
        :type scheme: str
        :param verbose: Log also rng and unit logs details
        :type verbose: bool
        :param ping: URI to ping with data
        :type ping: str
        """
        self.print = True
        self.path = path
        self.repository = None
        if repository:
            self.repository = repository
        self.branch = None
        if branch:
            self.branch = branch
        self.uuid = None
        if uuid:
            self.uuid = uuid
        self.workers = 1
        if workers:
            self.workers = workers
        self.ping = None
        if ping:
            self.ping = ping
        self.secret = bytes(secret, "utf-8")
        self.scheme = "tei"

        self.download = []

        if scheme:
            if scheme not in Test.SCHEMES:
                raise ValueError(
                    "Scheme {0} unknown, please use one of the following : {1}".format(
                        scheme,
                        ", ".join(Test.SCHEMES.keys())
                     )
                )
            self.scheme = scheme
        self.verbose = False
        if verbose:
            self.verbose = verbose

        self.results = defaultdict(dict)
        self.passing = defaultdict(dict)
        self.inventory = []
        self.status = "pending"  # Can be pending, success, failure, error
        self.files = []
        self.cts_files = []
        self.logs = []
        self.progress = None
        self.last = 0

    @property
    def successes(self):
        """ Get the number of successful tests

        :returns: Number of successful tests
        :rtype: int
        """
        return len([True for status in self.passing.values() if status is True])

    @property
    def json(self):
        """ Get Json representation of object report

        :return: JSON representing the complete test
        :rtype:
        """
        return json.dumps(self.report)

    @property
    def report(self):
        """ Get the report of the Test
        :return: Report of the test
        :rtype: dict
        """
        return {
            "status": self.successes == len(self.passing),
            "units": self.results,
            "coverage": statistics.mean([test["coverage"] for test in self.results.values()])
        }

    @property
    def directory(self):
        """ Directory
        :return: Path of the full directory
        :rtype: str
        """
        if self.repository:
            if self.uuid:
                return os.path.join(self.path, self.uuid)
            else:
                return os.path.join(self.path, self.repository.split("/")[-1])
        else:
            return self.path

    def write(self, data=None):
        """ Print data and flush the stdout to be able to retrieve information line by line on another tool

        :param data: Data to be printed
        :type data: str

        """
        if data is None:
            self.printing(self.download, flush=True)
        elif isinstance(data, str) and not data.isspace():
            if self.repository:
                data = data.replace(self.directory, self.repository)
            else:
                data = data.replace(self.directory, "")

            self.logs.append(data)

            if self.print:
                if self.ping:
                    dozen = len(self.logs)
                    if dozen > self.last + 49:
                        self.printing(self.logs[self.last:])
                        self.last = len(self.logs)
                else:
                    self.printing(data, flush=True)

    def flush(self):
        """ Flush the remaining logs to the endpoint """
        if self.ping and len(self.logs) > self.last + 1:
            self.printing(self.logs[self.last:])

    def printing(self, data, **kwargs):
        """ Decides to use HTTP connection or print system

        :return:
        """
        if self.ping:
            if isinstance(data, dict):
                data = json.dumps(data)
            else:
                data = json.dumps({"log": data})
            data = bytes(data, "utf-8")
            hashed = hmac.new(self.secret, data, hashlib.sha1).hexdigest()
            requests.post(
                self.ping,
                data=data,
                headers={"HookTest-Secure-X": hashed, "HookTest-UUID": self.uuid}
            )
        else:
            print(data, **kwargs)
        return True

    def send_report(self, report):
        """ Send the report through HTTP
        :param report:
        :return:
        """
        if self.ping is not None:
            return self.printing(report)

    def unit(self, filepath):
        """ Do test for a file and print the results

        :param filepath: Path of the file to be tested
        :type filepath: str

        :returns: List of status information
        :rtype: list
        """
        logs = []
        if filepath.endswith("__cts__.xml"):
            unit = HookTest.units.INVUnit(filepath)
            logs.append(">>>> Testing " + filepath)

            for name, status, unitlogs in unit.test():

                if status:
                    status_str = " passed"
                else:
                    status_str = " failed"

                logs.append(">>>>> " + name + status_str)

                if self.verbose and len(unitlogs) > 0:
                    logs.append("\n".join([log for log in unitlogs if log]))

                self.results[filepath][name] = status

            self.results[filepath] = Test.cover(self.results[filepath])
            self.passing[filepath.replace("/", ".")] = True == self.results[filepath]["status"]
            self.inventory += unit.urns

        else:
            unit = HookTest.units.CTSUnit(filepath)
            logs.append(">>>> Testing " + filepath.split("data")[-1])
            for name, status, unitlogs in unit.test(self.scheme, self.inventory):

                if status:
                    status_str = " passed"
                else:
                    status_str = " failed"

                logs.append(">>>>> " + name + status_str)

                if self.verbose and len(unitlogs) > 0:
                    logs.append("\n".join([log for log in unitlogs if log]))

                self.results[filepath][name] = status

            self.results[filepath] = Test.cover(self.results[filepath])
            self.passing[filepath.split("/")[-1]] = True == self.results[filepath]["status"]

        return logs + ["test+=1"]

    def run(self, printing=False):
        """ Run the tests

        :returns: Status of the test, List of logs, Report
        :rtype: (string, list, dict)
        """
        if printing is True:
            self.print = True

        self.files, self.cts_files = Test.files(self.directory)

        self.write(">>> Starting tests !")
        self.write("files="+str(len(self.files) + len(self.cts_files)))

        # We load a thread pool which has {self.workers} maximum workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            # We create a dictionary of tasks which
            tasks = {executor.submit(self.unit, target_file): target_file for target_file in self.cts_files}
            # We iterate over a dictionary of completed tasks
            for future in concurrent.futures.as_completed(tasks):
                logs = future.result()
                for log in logs:
                    self.write(log)

        # We load a thread pool which has 5 maximum workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            # We create a dictionary of tasks which
            tasks = {executor.submit(self.unit, target_file): target_file for target_file in self.files}
            # We iterate over a dictionary of completed tasks
            for future in concurrent.futures.as_completed(tasks):
                logs = future.result()
                for log in logs:
                    self.write(log)

        self.write(">>> Finished tests !")

        self.finish()
        self.write(
            "[{2}] {0} over {1} texts have fully passed the tests".format(
                self.successes, len(self.passing), self.status
            )
        )

        self.print = False

        self.flush()
        self.send_report()
        return self.status, self.logs, self.report

    def finish(self):
        """  Updated the status string based on available informations

        :return: Status string updated
        :rtype: str
        """

        if len(self.passing) != len(self.files + self.cts_files):
            self.status = "error"
        elif self.successes == len(self.passing):
            self.status = "success"
        else:
            self.status = "failure"
        return self.status

    def clone(self):
        """ Clone the repository

        :return: Indicator of success
        :rtype: bool
        """
        self.progress = Progress(parent=self)
        repo = git.repo.base.Repo.clone_from(
            url="https://github.com/{0}.git".format(self.repository),
            to_path=self.directory,
            progress=self.progress
        )

        if self.branch is None:
            self.branch = "master"

        if self.branch.isnumeric():
            ref = "refs/pull/{0}/head:refs/pull/origin/{0}".format(self.branch)
        else:
            ref = "refs/heads/{ref}".format(ref=self.branch)

        repo.remote().pull(ref, progress=self.progress)

        return repo is None

    def clean(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    @staticmethod
    def files(directory):
        """ Find CTS files in a directory
        :param directory: Path of the directory
        :type directory: str

        :returns: Path of xml text files, Path of __cts__.xml files
        :rtype: (list, list)
        """
        data = glob.glob(os.path.join(directory, "data/*/*/*.xml")) + glob.glob(os.path.join(directory, "data/*/*.xml"))
        return [f for f in data if "__cts__.xml" not in f], [f for f in data if "__cts__.xml" in f]

    @staticmethod
    def cover(test):
        """ Given a dictionary, compute the coverage of one item

        :param test: Dictionary where keys represents test done on a file and value a boolean indicating passing status
        :type test: boolean
        :returns: Passing status
        :rtype: dict
        """
        results = list(test.values())
        if len(results) > 0:
            return {
                "units": test,
                "coverage": len([v for v in results if v is True])/len(results)*100,
                "status": False not in results
            }
        else:
            return {
                "units": [],
                "coverage": 0,
                "status": False
            }


class Progress(git.RemoteProgress):
    """ Progress object for HookTest
    """
    def __init__(self, parent=None):
        super(Progress, self).__init__()
        self.parent = parent
        self.start = ["Cloning repository"]
        self.end = []
        self.download = ""
        self.progress = None

        self.current = 0
        self.maximum = 0

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.current = cur_count
        self.maximum = max_count

        if message:
            if message[-2:] == "/s":
                if self.progress is None:
                    self.progress = True
                self.download = message
            else:
                if self.progress:
                    self.progress = False
                    self.end.append(message)
                else:
                    self.start.append(message)

        if isinstance(self.parent, Test):
            self.parent.download = self.json
            self.parent.write()

    @property
    def json(self):
        return [
            "\n".join(self.start),
            "Downloaded {0}/{1} ({2})".format(self.current, self.maximum, self.download),
            "\n".join(self.end)
        ]