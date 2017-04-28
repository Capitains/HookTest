import re
from collections import defaultdict

import pkg_resources
from lxml import etree


class TESTUnit(object):
    """ TestUnit Metaclass

    :param path: path of the current file
    """

    EPIDOC = pkg_resources.resource_filename("HookTest", "resources/epidoc.rng")
    TEI_ALL = pkg_resources.resource_filename("HookTest", "resources/tei.rng")
    JING = pkg_resources.resource_filename("jingtrang", "jing.jar")
    RNG_ERROR = re.compile("([0-9]+):([0-9]+):(.*);")
    RNG_FAILURE = re.compile("([0-9]+):([0-9]+):(\s*fatal.*)")
    SPACE_REPLACER = re.compile("(\s{2,})")
    FORBIDDEN_CHAR = re.compile("[^\w\d]")
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


