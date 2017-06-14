# -*- coding: utf-8 -*-

import os
import glob
import statistics
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
from prettytable import PrettyTable as PT
from prettytable import ALL as pt_all

import HookTest.capitains_units.cts
import HookTest.units
from colors import white, magenta, black
from operator import attrgetter


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
    :type verbose: int
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
        "epidoc": "epidoc.rng",
        "tei-ignore": "tei.rng",
        "epidoc-ignore": "epidoc.rng"
    }

    def __init__(
            self, path,
            repository=None, branch=None, uuid=None, workers=1, scheme="tei",
            verbose=0, ping=None, secret="", triggering_size=None, console=False, build_manifest=False,
            finder=DefaultFinder, finderoptions=None, countwords=False, allowfailure=False,
            from_travis_to_hook=False, timeout=30,
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
        :type verbose: int
        :param ping: URI to ping with data
        :type ping: str
        :param console: If set to true, print logs to the console
        :type console: bool
        :param countwords: Count the number of words for passing texts
        :type countwords: bool
        :param build_manifest: Build a manifest at the end of the test
        :type build_manifest: bool
        """
        self.depth = 10
        self.console = console
        self.build_manifest = build_manifest
        self.path = path
        self.repository = repository
        self.branch = branch
        self.uuid = uuid
        self.workers = workers
        self.ping = ping
        if os.environ.get("HOOK_SECRET"):
            self.secret = os.environ.get("HOOK_SECRET").encode()
        else:
            self.secret = bytes(secret, "utf-8")
        self.scheme = scheme
        self.verbose = verbose
        self.countwords = countwords
        self.allowfailure = allowfailure
        self.__triggering_size = None
        self.timeout = timeout
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

        self.from_travis_to_hook = from_travis_to_hook

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
        elif self.allowfailure is True and self.count_files > 0 and self.successes > 0:
            return Test.SUCCESS
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
        """ Flush the remaining logs to the endpoint

        """
        if len(stack) > 0:
            for needle in stack:
                needle.sent = True
            self.send({"units": [needle.dict for needle in stack]})

    def send(self, data):
        """ Send data to self.ping URL

        :param data: Data to send
        :return: Result of request
        """
        if isinstance(data, dict):
            data = Test.dump(data)
        else:
            data = Test.dump({"logs": data})

        data = bytes(data, "utf-8")
        hashed = hmac.new(self.secret, data, hashlib.sha1).hexdigest()
        return requests.post(
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
            unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit(filepath)
            texttype = "CTSMetadata"
            logs.append(">>>> Testing " + filepath)
            for name, status, unitlogs in unit.test():

                if status:
                    status_str = " passed"
                else:
                    status_str = " failed"

                logs.append(">>>>> " + name + status_str)

                if self.verbose > 0 and len(unitlogs) > 0:
                    logs += [log for log in unitlogs if log]

                results[name] = status
            additional += unit.urns

        else:
            unit = HookTest.capitains_units.cts.CTSText_TestUnit(filepath, countwords=self.countwords, timeout=self.timeout)
            texttype = "CTSText"
            logs.append(">>>> Testing " + filepath.split("data")[-1])
            for name, status, unitlogs in unit.test(self.scheme, self.inventory):

                if status:
                    status_str = " passed"
                else:
                    status_str = " failed"

                logs.append(">>>>> " + name + status_str)

                if self.verbose > 0 and len(unitlogs) > 0:
                    logs += [log for log in unitlogs if log]

                results[name] = status
            additional = {}
            additional["citations"] = unit.citation
            additional["duplicates"] = unit.duplicates
            additional["forbiddens"] = unit.forbiddens
            additional['language'] = unit.lang
            if self.countwords:
                additional["words"] = unit.count
        return self.cover(filepath, results, testtype=texttype, logs=logs, additional=additional), filepath, additional

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
            self.middle()  # To print the results from the metadata file tests

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
        if self.console == "table":
            if isinstance(log, UnitLog):
                if log.status is True:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                else:
                    sys.stdout.write('X')
                    sys.stdout.flush()
        elif self.console == "inline":
            print(str(log), flush=True)
        elif self.ping and len(self.stack) >= self.triggering_size:
            self.flush(self.stack)

    def start(self):
        """ Deal with the start of the process

        """
        if self.console is not False:
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
        """ Information to send or print during download

        """
        if self.console is not False and self.verbose == 10:
            print("\n".join([f for f in self.progress.json if f]), flush=True)

    def middle(self):
        """ to print out the results for the metadata files that failed the tests

        :return:
        :rtype:
        """
        self.m_files = self.m_passing = len(self.results.values())

        if self.console == "table" and self.verbose > 0:
            print('', flush=True)
            if False not in [unit.status for unit in self.results.values()]:
                print('All Metadata Files Passed', flush=True)
            else:
                display_table = PT(["Filename", "Failed Tests"])
                display_table.align["Filename", "Failed Tests"] = 'c'
                display_table.hrules = pt_all
                for unit in sorted(self.report['units'], key=lambda x: x['name']):
                    if unit['status'] is not True:
                        self.m_passing -= 1
                        display_table.add_row([unit['name'], '\n'.join(['{test} failed'.format(test=x) for x in unit['units'] if unit['units'][x] is False])])
                print(display_table, flush=True)

    def end(self):
        """ Deal with end logs
        """
        total_units = 0
        total_words = 0
        language_words = defaultdict(int)
        show = list(HookTest.capitains_units.cts.CTSText_TestUnit.readable.values())
        if self.verbose == 0:
            show.remove("Duplicate passages")
            show.remove("Forbidden characters")
        if self.console is not False:
            if self.console == "table":
                duplicate_nodes = ''
                forbidden_chars = ''
                num_texts = 0
                num_failed = 0
                print('', flush=True)

                if self.countwords is True:
                    display_table = PT(["Identifier", "Words", "Nodes", "Failed Tests"])
                    display_table.align["Identifier", "Words", "Nodes", "Failed Tests"] = "c"
                else:
                    display_table = PT(["Identifier", "Nodes", "Failed Tests"])
                    display_table.align["Identifier", "Nodes", "Failed Tests"] = "c"

                display_table.hrules = pt_all
                # try using self.results and then the UnitLog attributes instead of self.report
                # also use operator.attrgetter('name') instead of lambda x in the for statement
                for unit in sorted(self.results.values(), key=attrgetter('name')):
                    if not unit.name.endswith('__cts__.xml'):
                        num_texts += 1
                        if unit.units["Passage level parsing"] is False:
                            try:
                                show.remove("Duplicate passages")
                                show.remove("Forbidden characters")
                            except:
                                pass
                        if unit.coverage != 100.0:
                            num_failed += 1
                            text_color = magenta
                        else:
                            text_color = white

                        if unit.coverage == 0.0:
                            failed_tests = 'All'
                        else:
                            failed_tests = '\n'.join([x for x in unit.units if unit.units[x] is False and x in show])

                        if unit.additional['duplicates']:
                            duplicate_nodes += '\t{name}\t{nodes}\n'.format(name=magenta(os.path.basename(unit.name)),
                                                                          nodes=', '.join(unit.additional['duplicates']))
                        if unit.additional['forbiddens']:
                            forbidden_chars += '\t{name}\t{nodes}\n'.format(name=magenta(os.path.basename(unit.name)),
                                                                          nodes=', '.join(unit.additional['forbiddens']))

                        if self.verbose >= 7 or unit.status is False:
                            if self.countwords:
                                row = [
                                    "{}".format(text_color(os.path.basename(unit.name))),
                                     "{:,}".format(unit.additional['words']),
                                     ';'.join([str(x[1]) for x in unit.additional['citations']]),
                                     failed_tests
                                ]
                            else:
                                row = [
                                    "{}".format(text_color(os.path.basename(unit.name))),
                                     ';'.join([str(x[1]) for x in unit.additional['citations']]),
                                     failed_tests
                                ]
                            display_table.add_row(row)

                        for x in unit.additional['citations']:
                            total_units += x[1]

                        if self.countwords:
                            total_words += unit.additional['words']
                            if unit.additional['words'] > 0:
                                language_words[unit.additional['language']] += unit.additional['words']

                print(display_table, flush=True)
                print('', flush=True)
                if self.verbose >= 5:
                    if duplicate_nodes:
                        duplicate_nodes = magenta('Duplicate nodes found:\n') + duplicate_nodes + '\n'
                    if forbidden_chars:
                        forbidden_chars = magenta('Forbidden characters found:\n') + forbidden_chars + '\n'
                else:
                    duplicate_nodes = forbidden_chars = ''

                print("{dupes}{forbs}>>> End of the test !\n".format(dupes=duplicate_nodes, forbs=forbidden_chars))
                t_pass = num_texts - num_failed
                cov = round(statistics.mean([test.coverage for test in self.results.values()]), ndigits=2)
                results_table = PT(["HookTestResults", ""])
                results_table.align["HookTestResults", ""] = "c"
                results_table.hrules = pt_all
                results_table.add_row(["Total Texts", num_texts])
                results_table.add_row(["Passing Texts", t_pass])
                results_table.add_row(["Metadata Files", self.m_files])
                results_table.add_row(["Passing Metadata", self.m_passing])
                results_table.add_row(["Coverage", cov])
                results_table.add_row(["Total Citation Units", "{:,}".format(total_units)])
                if self.countwords is True:
                    results_table.add_row(["Total Words", "{:,}".format(total_words)])
                    for l, words in language_words.items():
                        results_table.add_row(["Words in {}".format(l.upper()), "{:,}".format(words)])
                print(results_table, flush=True)

                # Pushing to HOOK !
                if isinstance(self.from_travis_to_hook, str):
                    args = [num_texts, t_pass, self.m_files, self.m_passing, cov, total_units]
                    if self.countwords is True:
                        args.append(language_words)
                    print(self.send_to_hook_from_travis(*args).text)

                #Manifest of passing files
                if self.build_manifest:
                    passing = self.create_manifest()
                    with open('{}/manifest.txt'.format(self.path), mode="w") as f:
                        f.write('\n'.join(passing))
            else:
                print(
                    ">>> End of the test !\n" \
                    ">>> [{2}] {0} out of {1} files did not pass the tests".format(
                        len(self.passing) - self.successes, len(self.passing), self.status
                    ),
                    flush=True
            )
        elif self.ping:
            report = self.report
            report["units"] = [unit.dict for unit in self.stack]
            self.send(report)

    def send_to_hook_from_travis(
            self, texts_total, texts_passing,
            metadata_total, metadata_passing,
            coverage, nodes_count,
            words_dict=None
    ):
        """ Send data to travis

        :return: Request output
        """
        data = dict(
            # Event
            event_type=os.environ.get("TRAVIS_EVENT_TYPE"),

            build_uri="https://travis-ci.org/{slug}/builds/{bid}".format(
                bid=os.environ.get("TRAVIS_BUILD_ID"),
                slug=os.environ.get("TRAVIS_REPO_SLUG")
            ),
            build_id=os.environ.get("TRAVIS_BUILD_NUMBER"),
            commit_sha=os.environ.get("TRAVIS_COMMIT"),

            # Information about the test
            texts_total=texts_total,
            texts_passing=texts_passing,
            metadata_total=metadata_total,
            metadata_passing=metadata_passing,
            coverage=coverage,
            nodes_count=nodes_count,
            units={
                unit_name: log.status for unit_name, log in self.results.items()
            },
        )
        if data["event_type"] == "pull_request":
            data["source"] = os.environ.get("TRAVIS_PULL_REQUEST")
        else:
            data["source"] = os.environ.get("TRAVIS_BRANCH")

        if words_dict is not None:
            data["words_count"] = words_dict

        data = Test.dump(data)
        data = bytes(data, "utf-8")
        hashed = hmac.new(self.secret, data, hashlib.sha1).hexdigest()
        return requests.post(
            self.from_travis_to_hook,
            data=data,
            headers={
                "HookTest-Secure-X": hashed,
                "Content-Type": "application/json"
            }
        )

    def create_manifest(self):
        """ Creates a manifest.txt file in the source directory that contains an ordered list of passing files
        """
        passing_temp = [x.name for x in self.results.values() if x.coverage == 100.0]
        passing = []
        for f in passing_temp:
            if not f.endswith('__cts__.xml') and '{}/__cts__.xml'.format(
                    os.path.dirname(f)) in passing_temp and '{}/__cts__.xml'.format(
                    '/'.join(f.split('/')[:-2])) in passing_temp:
                passing.append(f)
                passing.append('{}/__cts__.xml'.format(os.path.dirname(f)))
                passing.append('{}/__cts__.xml'.format('/'.join(f.split('/')[:-2])))
        return sorted(list(set(passing)))

    def clone(self):
        """ Clone the repository

        :return: Indicator of success
        :rtype: bool
        """
        self.progress = Progress(parent=self)
        repo = git.repo.Repo.init(self.directory, mkdir=True)
        repo.create_remote("origin", url="https://github.com/{0}.git".format(self.repository))

        if self.branch is None:
            self.branch = "refs/heads/master"

        if pr_finder.match(self.branch):
            ref = "refs/{0}".format(self.branch)
        else:
            ref = self.branch
        if git.cmd.Git().version_info >= (2, 9, 0, 0):
            repo.remote().pull(
                ref, progress=self.progress, allow_unrelated_histories=True, depth=self.depth
            )
        else:
            repo.remote().pull(
                ref, progress=self.progress, depth=self.depth
            )

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

    def cover(self, name, test, testtype=None, logs=None, additional=None):
        """ Given a dictionary, compute the coverage of one item

        :param name:
        :type name:
        :param test: Dictionary where keys represents test done on a file and value a boolean indicating passing status
        :type test: boolean
        :param logs: List of logs for one unit
        :type logs: list
        :param testtype: the type of file tested (e.g., CTSMetadata or CTSText)
        :type testtype: str
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
                additional=additional,
                testtype=testtype
            )
        else:
            return UnitLog(
                directory=self.directory,
                name=name,
                units=list(),
                coverage=0.0,
                status=False,
                logs=logs,
                repository=self.repository,
                testtype=testtype
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
            elif console:
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
        elif console:
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

    def __init__(self, directory, name, units, coverage, status, testtype=None, logs=None, sent=False, repository=None, additional=None
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
        self.testtype = testtype
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
        elif self.directory != ".":
            return data.replace(self.directory, "")
        else:
            return data

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
