# -*- coding: utf-8 -*-

import os
import glob
import statistics#
import sys
import traceback
import re

from collections import defaultdict, OrderedDict
from multiprocessing.pool import Pool
import json
import git
import shutil
import requests
import hashlib
import hmac
import time

import HookTest.units


pr_finder = re.compile("pull\/([0-9]+)\/head")


class DefaultFinder(object):
    """ Finder are object used in Test to retrieve the target files of the tests

    """
    def __init__(self, **options):
        pass

    def find(self, directory):
        """ Return object to find

        :param directory: Root Directory to search in

        :returns: Path of xml text files, Path of __cts__.xml files
        :rtype: (list, list)
        """
        data = glob.glob(os.path.join(directory, "data/*/*/*.xml")) + glob.glob(os.path.join(directory, "data/*/*.xml"))
        files, cts = [f for f in data if "__cts__.xml" not in f], [f for f in data if "__cts__.xml" in f]

        # For unit testing and human readable progression
        cts.sort()
        files.sort()
        return files, cts


class FilterFinder(DefaultFinder):
    """ FilterFinder provide a filtering capacity to DefaultFinder.

    It takes an include option which takes the form of the work urn (*ie.* in urn:cts:latinLit:phi1294.phi002.perseus-lat2 \
    this would be phi1294.phi002.perseus-lat2, cut at any of the points : phi1294, phi1294.phi002, phi1294.phi002.perseus-lat2)

    :param include: Representation of the work urn component (might be from one member down to the version member)
    :type include: str
    """
    def __init__(self, include, **options):
        self.include = include.split(".")

    def find(self, directory):
        """ Return object to find

        :param directory: Root Directory to search in

        :returns: Path of xml text files, Path of __cts__.xml files
        :rtype: (list, list)
        """
        textgroup, work, version = "*", "*", "*.*.*",
        if len(self.include) == 3:
            version = ".".join(self.include)
        if len(self.include) >= 2:
            work = self.include[1]
        if len(self.include) >= 1:
            textgroup = self.include[0]

        cts = glob.glob(os.path.join(directory, "data/{textgroup}/__cts__.xml".format(
            textgroup=textgroup
        ))) + \
              glob.glob(os.path.join(directory, "data/{textgroup}/{work}/__cts__.xml".format(
                  textgroup=textgroup, work=work
              )))
        files = glob.glob(os.path.join(directory, "data/{textgroup}/{work}/{version}.xml".format(
            textgroup=textgroup, work=work, version=version
        )))
        # For unit testing and human readable progression
        cts.sort()
        files.sort()
        return files, cts


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
    :param ping: URI to ping with data
    :type ping: str
    :param console: If set to true, print logs to the console
    :type console: bool
    :param finder: Test files retriever
    :type finder: DefaultFinder
    :param finderoptions: Dictionary of option to instantiate specific finders
    :type finderoptions: dict
    :param countwords: Enable counting words for text tests (False by default)
    :type countwords: bool
    """
    STACK_TRIGGER_SIZE = 10
    FAILURE = "failed"
    ERROR = "error"
    SUCCESS = "success"
    PENDING = "pending"
    SCHEMES = {
        "tei": "tei.rng",
        "epidoc": "epidoc.rng"
    }

    def __init__(self, path,
         repository=None, branch=None, uuid=None, workers=1, scheme="tei",
         verbose=False, ping=None, secret="", triggering_size=None, console=False,
         finder=DefaultFinder, finderoptions=None, countwords=False,
        **kwargs
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
        :param console: If set to true, print logs to the console
        :type console: bool
        """
        self.depth = 10
        self.console = console
        self.path = path
        self.repository = repository
        self.branch = branch
        self.uuid = uuid
        self.workers = workers
        self.ping = ping
        self.secret = bytes(secret, "utf-8")
        self.scheme = scheme
        self.verbose = verbose
        self.countwords = countwords
        self.__triggering_size = None
        if isinstance(triggering_size, int):
            self.__triggering_size = triggering_size

        if scheme is not "tei" and scheme not in Test.SCHEMES:
            raise ValueError(
                "Scheme {0} unknown, please use one of the following : {1}".format(
                    scheme,
                    ", ".join(Test.SCHEMES.keys())
                )
            )

        self.results = OrderedDict()
        self.passing = defaultdict(bool)
        self.inventory = []
        self.text_files = []
        self.cts_files = []
        self.progress = None

        self.finder = finder
        if not finder:
            self.finder = DefaultFinder
        if finderoptions:
            self.finder = self.finder(**finderoptions)
        else:
            self.finder = self.finder()

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
        return Test.dump(self.report)

    @property
    def report(self):
        """ Get the report of the Test
        :return: Report of the test
        :rtype: dict
        """
        coverage = 0
        if len(self.results) > 0:
            coverage = statistics.mean([test.coverage for test in self.results.values()])
        return {
            "status": self.status,
            "units": [unitlog.dict for unitlog in self.results.values()],
            "coverage": coverage
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

    @property
    def stack(self):
        """ Get the current stack of unsent item

        :return: Unset UnitLog
        :rtype: [UnitLog]
        """
        return [result for result in self.results.values() if result.sent is False]

    @property
    def status(self):
        """  Updated the status string based on available informations

        :return: Status string updated
        :rtype: str
        """

        if self.count_files == 0 or len(self.passing) != self.count_files:
            return Test.ERROR
        elif self.count_files > 0 and self.successes == len(self.passing):
            return Test.SUCCESS
        else:
            return Test.FAILURE

    @property
    def triggering_size(self):
        """

        :return:
        """
        percentage = int(self.count_files / 20)

        if self.__triggering_size is not None:
            return self.__triggering_size
        elif percentage > Test.STACK_TRIGGER_SIZE:
            return percentage
        else:
            return Test.STACK_TRIGGER_SIZE

    @property
    def files(self):
        return self.text_files, self.cts_files

    @property
    def count_files(self):
        return len(self.text_files) + len(self.cts_files)

    def flush(self, stack):
        """ Flush the remaining logs to the endpoint """
        if len(stack) > 0:
            for needle in stack:
                needle.sent = True
            self.send({"units": [needle.dict for needle in stack]})

    def send(self, data):
        """

        :param data:
        :return:
        """
        if isinstance(data, dict):
            data = Test.dump(data)
        else:
            data = Test.dump({"logs": data})

        data = bytes(data, "utf-8")
        hashed = hmac.new(self.secret, data, hashlib.sha1).hexdigest()
        requests.post(
            self.ping,
            data=data,
            headers={"HookTest-Secure-X": hashed, "HookTest-UUID": self.uuid}
        )

    def unit(self, filepath):
        """ Do test for a file and print the results

        :param filepath: Path of the file to be tested
        :type filepath: str
        :returns: A UnitLog
        :rtype: UnitLog
        """
        logs = []
        results = {}
        additional = []
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
                    logs += [log for log in unitlogs if log]

                results[name] = status
            additional += unit.urns

        else:
            unit = HookTest.units.CTSUnit(filepath, countwords=self.countwords)
            logs.append(">>>> Testing " + filepath.split("data")[-1])
            for name, status, unitlogs in unit.test(self.scheme, self.inventory):

                if status:
                    status_str = " passed"
                else:
                    status_str = " failed"

                logs.append(">>>>> " + name + status_str)

                if self.verbose and len(unitlogs) > 0:
                    logs += [log for log in unitlogs if log]

                results[name] = status
            additional = {}
            if self.countwords:
                additional["words"] = unit.count
        return self.cover(filepath, results, logs=logs, additional=additional), filepath, additional

    def run(self):
        """ Run the tests

        :returns: Status of the test, List of logs, Report
        :rtype: (string, list, dict)
        """

        self.text_files, self.cts_files = self.find()
        self.start()
        # We deal with Inventory files first to get a list of urns

        with Pool(processes=self.workers) as executor:
            # We iterate over a dictionary of completed tasks
            for future in executor.imap_unordered(self.unit, [file for file in self.cts_files]):
                result, filepath, additional = future
                self.results[filepath] = result
                self.passing[filepath] = result.status
                self.inventory += additional
                self.log(self.results[filepath])

            # Required for coverage
            executor.close()
            executor.join()

        # We load a thread pool which has 5 maximum workers
        with Pool(processes=self.workers) as executor:
            # We create a dictionary of tasks which
            for future in executor.imap_unordered(self.unit, [file for file in self.text_files]):
                result, filepath, additional = future
                self.results[filepath] = result
                self.passing[filepath] = result.status
                self.log(self.results[filepath])

            # Required for coverage
            executor.close()
            executor.join()
        self.end()
        return self.status

    def log(self, log):
        """ Deal with middle process situation

        :param log: Result of a test for one unit
        :type log: UnitLog
        :return: None
        """
        if self.console:
            print(str(log), flush=True)
        elif self.ping and len(self.stack) >= self.triggering_size:
            self.flush(self.stack)

    def start(self):
        """ Deal with the start of the process

        """
        if self.console:
            print(">>> Starting tests !", flush=True)
            print(">>> Files to test : "+str(self.count_files), flush=True)
        elif self.ping:
            self.send({
                "logs": [
                    ">>> Starting tests !"
                ],
                "files": self.count_files,
                "texts": len(self.text_files),
                "inventories": len(self.cts_files)
            })

    def download(self):
        if self.console:
            print("\n".join([f for f in self.progress.json if f]), flush=True)

    def end(self):
        """ Deal with end logs
        """
        if self.console:
            print(
                ">>> End of the test !\n" \
                ">>> [{2}] {0} over {1} texts have fully passed the tests".format(
                    self.successes, len(self.passing), self.status
                ),
                flush=True
            )
        elif self.ping:
            report = self.report
            report["units"] = [unit.dict for unit in self.stack]
            self.send(report)

    def clone(self):
        """ Clone the repository

        :return: Indicator of success
        :rtype: bool
        """
        self.progress = Progress(parent=self)
        repo = git.repo.base.Repo.clone_from(
            url="https://github.com/{0}.git".format(self.repository),
            to_path=self.directory,
            progress=self.progress,
            depth=self.depth
        )

        if self.branch is None:
            self.branch = "refs/heads/master"

        if pr_finder.match(self.branch):
            ref = "refs/{0}".format(self.branch)
        else:
            ref = self.branch

        repo.remote().pull(ref, progress=self.progress)

        return repo is None

    def clean(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    def find(self):
        """ Find CTS files in a directory
        :param directory: Path of the directory
        :type directory: str

        :returns: Path of xml text files, Path of __cts__.xml files
        :rtype: (list, list)
        """

        return self.finder.find(self.directory)

    def cover(self, name, test, logs=None, additional=None):
        """ Given a dictionary, compute the coverage of one item

        :param name:
        :type name:
        :param test: Dictionary where keys represents test done on a file and value a boolean indicating passing status
        :type test: boolean
        :param logs: List of logs for one unit
        :type logs: list
        :returns: Passing status
        :rtype: dict
        """
        results = list(test.values())
        if logs is None:
            logs = list()

        if len(results) > 0:
            return UnitLog(
                directory=self.directory,
                name=name,
                units=test,
                coverage=len([v for v in results if v is True])/len(results)*100,
                status=False not in results,
                logs=logs,
                repository=self.repository,
                additional=additional
            )
        else:
            return UnitLog(
                directory=self.directory,
                name=name,
                units=list(),
                coverage=0.0,
                status=False,
                logs=logs,
                repository=self.repository
            )

    @staticmethod
    def dump(obj):
        return json.dumps(obj, separators=(',', ':'), sort_keys=True)


def cmd(console=False, **kwargs):
    """ Generate the complete process of Test

    :param console: Print logs to console
    :type console: bool
    :param kwargs: Named arguments
    :type kwargs: dict
    :return: Status of the test

    """
    test = HookTest.test.Test(console=console, **kwargs)
    test.console = console

    if test.ping:
        test.send({"status": "download"})

    if "repository" in kwargs and kwargs["repository"]:
        try:
            test.clone()
        except Exception as E:
            type_, value_, traceback_ = sys.exc_info()
            tb = "".join(traceback.format_exception(type_, value_, traceback_))
            if test.ping:
                test.send({"status": Test.ERROR, "message": tb})
            elif console is True:
                print(tb, flush=True)
            test.clean()
            raise(E)

    if test.ping:
        test.send({"status": "pending"})

    status = {}

    try:
        status = test.run()
    except Exception as E:
        type_, value_, traceback_ = sys.exc_info()
        tb = "".join(traceback.format_exception(type_, value_, traceback_))
        if test.ping:
            test.send({"status": Test.ERROR, "message": tb})
        elif console is True:
            print(tb, flush=True)

    if "repository" in kwargs and kwargs["repository"]:
        test.clean()

    if "json" in kwargs and kwargs["json"]:
        with open(kwargs["json"], "w") as json_file:
            json.dump(test.report, json_file)

    return status


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
            self.parent.download()

    @property
    def json(self):
        return [
            "\n".join(self.start),
            "Downloaded {0}/{1} ({2})".format(self.current, self.maximum, self.download),
            "\n".join(self.end)
        ]


class UnitLog(object):
    """ Model for logging information

    :param name: Name of the tested unit
    :param units:
    :param coverage: Percentage of successful tests
    :param status: Status of the unit
    :param logs: Logs
    :param sent: Status regarding the logging
    :param repository: Repository
    :param additional: Additional informations. Can be used for words counting
    """

    def __init__(self, directory, name, units, coverage, status, logs=None, sent=False, repository=None, additional=None
                 ):
        """ Initiate the object

        :param name: Name of the tested unit
        :param units:
        :param coverage: Percentage of successful tests
        :param status: Status of the unit
        :param logs: Logs
        :param sent: Status regarding the logging
        """
        self.directory = directory
        self.units = units
        self.coverage = coverage
        self.status = status
        self.__logs = list()
        self.sent = sent
        self.time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.repository = repository

        self.name = self.directory_replacer(name)
        self.logs = logs
        self.additional = {}
        if isinstance(additional, dict):
            self.additional = additional

    @property
    def logs(self):
        return self.__logs

    @logs.setter
    def logs(self, logs):
        if isinstance(logs, list):
            self.__logs = [self.directory_replacer(data) for data in logs]

    def directory_replacer(self, data):
        if self.repository:
            return data.replace(self.directory, self.repository)
        else:
            return data.replace(self.directory, "")

    @property
    def dict(self):
        """ Get the dictionary version of the object

        :return: Dictionary representation of the object
        :rtype: dict
        """
        x = {
            "name": self.name,
            "units": self.units,
            "coverage": self.coverage,
            "status": self.status,
            "logs": self.logs,
            "at": self.time
        }
        x.update(self.additional)
        return x

    def __str__(self):
        return "\n".join(self.logs)
