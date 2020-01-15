import re
from collections import defaultdict

import pkg_resources
from lxml import etree
import subprocess
from threading import Timer
from hashlib import md5
import time
import requests
import shutil
from lxml.etree import parse
import validators
from os import makedirs
import os.path


class TESTUnit(object):
    """ TestUnit Metaclass

    :param path: path of the current file
    """

    EPIDOC = pkg_resources.resource_filename("HookTest", "resources/epidoc.rng")
    TEI_ALL = pkg_resources.resource_filename("HookTest", "resources/tei.rng")
    JING = pkg_resources.resource_filename("jingtrang", "jing.jar")
    RNG_ERROR = re.compile(r"([0-9]+):([0-9]+):(.*)")
    RNG_FAILURE = re.compile(r"([0-9]+):([0-9]+):(\s*fatal.*)")
    SPACE_REPLACER = re.compile(r"(\s{2,})")
    FORBIDDEN_CHAR = re.compile(r"[^\w\d]")
    NS = {"tei": "http://www.tei-c.org/ns/1.0", "ti": "http://chs.harvard.edu/xmlns/cts"}
    PARSER = etree.XMLParser(no_network=True, resolve_entities=False)

    def __init__(self, path):
        self.path = path
        self.xml = None
        self.testable = True
        self.__logs = []
        self.__archives = []
        self.Text = False
        self.urn = None

    @property
    def logs(self):
        return self.__logs

    def log(self, message):
        if isinstance(message, str) and not message.isspace() and len(message) > 0:
            self.__logs.append(">>>>>> " + TESTUnit.SPACE_REPLACER.sub(" ", message.lstrip()))

    def error(self, error):
        if isinstance(error, Exception):
            self.log(str(type(error)) + " : " + str(error))

    def flush(self):
        self.__archives = self.__archives + self.__logs
        self.__logs = []

    def parsable(self):
        """ Check and parse the xml file

        :returns: Indicator of success and messages
        :rtype: boolean
        """
        try:
            with open(self.path) as f:
                xml = etree.parse(f, TESTUnit.PARSER)
                self.xml = xml
                self.testable = True
                self.log("Parsed")
        except Exception as e:
            self.testable = False
            self.error(e)
        finally:
            yield self.testable

    @staticmethod
    def rng(line):
        """ Return a rng free line

        :param line: Line of logs
        :return: LineColumn code, Error
        :rtype: (str, str)
        """
        found = TESTUnit.RNG_ERROR.findall(line)
        identifier, code = "", line

        if len(found) == 0:
            found = TESTUnit.RNG_FAILURE.findall(line)

        if len(found) > 0:
            identifier, code = "(L{0} C{1})".format(*found[0]), found[0][-1]

        return code, identifier

    @staticmethod
    def rng_logs(logs):
        """ Return a rng free line

        :param logs: Sum of logs
        :type logs: str or bytes
        :return: LineColumn code, Error
        :rtype: (str, str)
        """
        logs = [TESTUnit.rng(log) for log in logs.decode("utf-8").split("\n") if bool(log.strip())]
        filtered_logs = defaultdict(list)

        for key, value in logs:
            filtered_logs[key].append(value)

        for key, value in filtered_logs.items():
            yield "{0} [In {1}]".format(key, "; ".join(value))

    def run_rng(self, rng_path):
        """ Run the RNG through JingTrang

        :param rng_path: Path to the RelaxNG file to run against the XML to test
        """
        test = subprocess.Popen(
            ["java", "-Duser.country=US", "-Duser.language=en", "-jar", TESTUnit.JING, rng_path, self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )
        out = []
        error = []
        timer = Timer(self.timeout, test.kill)
        try:
            timer.start()
            out, error = test.communicate()
        except Exception as E:
            self.error(E)
            yield False
            pass
        finally:
            if not timer.is_alive():
                self.log("Timeout on RelaxNG")
                yield False
                timer.cancel()
                pass
            timer.cancel()

        # This is to deal with Travis printing a message about the _JAVA_OPTIONS when a java command is run
        # Travis printing this command resulted in this test not passing
        out = '\n'.join([x for x in out.decode().split('\n') if '_JAVA_OPTIONS' not in x]).encode()
        error = '\n'.join([x for x in error.decode().split('\n') if '_JAVA_OPTIONS' not in x]).encode()

        if len(out) > 0:
            for issue in TESTUnit.rng_logs(out):
                self.log(issue)
                self.dtd_errors.append(issue)
        yield len(out) == 0 and len(error) == 0

    def auto_rng(self):
        xml = parse(self.path)
        xml_dir = os.path.dirname(os.path.abspath(self.path))
        # A file can have multiple schema
        rngs = xml.xpath("/processing-instruction('xml-model')")
        if len(rngs) == 0:
            raise FileNotFoundError
        for rng in rngs:
            uri = rng.attrib["href"]
            rng_path = os.path.abspath(os.path.join(xml_dir, uri))
            if validators.url(uri):
                rng_path = self.get_remote_rng(uri)
            elif not os.path.isfile(rng_path):
                self.dtd_errors.append("No RNG was found at " + rng_path)
                yield False
                continue
            for status in self.run_rng(rng_path):
                yield status

    def get_remote_rng(self, url):
        """ Given a valid URL, downloads the RNG from the given URL and returns the filepath and name

        :param url: the URL of the RNG
        :return: filenpath and name where the RNG was saved
        """
        # If the file is remote, have a file-system approved name
        # The md5 hash seems like a good option
        sha = md5(url.encode()).hexdigest()

        # We have a name for the rng file but also for the in-download marker
        # Note : we might want to add a os.makedirs somewhere with exists=True
        makedirs(".rngs", exist_ok=True)
        stable_local = os.path.join(".rngs", sha + ".rng")
        stable_local_downloading = os.path.join(".rngs", sha + ".rng-indownload")

        # check if the stable_local rng already exists
        # if it does, immediately run the rng test and move to the next rng in the file
        if os.path.exists(stable_local):
            return stable_local
        # We check if the in-download proof file is shown here
        # Until the in-download marker is there, we need to wait
        elif os.path.exists(stable_local_downloading):
            # Wait up to 30 secs ?
            # Have it as a constant that could be changed in environment variables ?
            waited = self.timeout
            while not os.path.exists(stable_local):
                time.sleep(1)
                waited -= 1
                if waited < 0:
                    # Maybe we can wait more ?
                    raise EnvironmentError("The download of the RNG took too long")
        else:
            with open(stable_local_downloading, "w") as f:
                f.write("Downloading...")
            data = requests.get(url)
            data.raise_for_status()
            with open(stable_local_downloading, "w") as f:
                f.write(data.text)
            shutil.move(stable_local_downloading, stable_local)

        return stable_local
