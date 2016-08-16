from lxml import etree
import warnings
import MyCapytain.resources.texts.local
import MyCapytain.resources.inventory
import MyCapytain.common.reference
import MyCapytain.errors
import pkg_resources
import subprocess
import re
from collections import defaultdict
from lxml.etree import XPathEvalError

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
            f = open(self.path)
            xml = etree.parse(f, TESTUnit.PARSER)
            self.xml = xml
            self.testable = True
            self.log("Parsed")
            f.close()
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


class INVUnit(TESTUnit):
    """ CTS testing object

    :param path: Path to the file
    :type path: basestring
    """

    tests = ["parsable", "capitain", "metadata", "check_urns"]
    readable = {
        "parsable": "File parsing",
        "capitain": "MyCapytain parsing",
        "metadata": "Metadata availability",
        "check_urns": "URNs testing"
    }

    def __init__(self, *args, **kwargs):
        super(INVUnit, self).__init__(*args, **kwargs)
        self.urns = []
        self.type = None

    def capitain(self):
        """ Load the file in MyCapytain
        """
        if self.xml:
            textgroup = "textgroup" in self.xml.getroot().tag
            work = not textgroup and "work" in self.xml.getroot().tag
            if textgroup:
                self.type = "textgroup"
                self.log("TextGroup detected")
                self.Text = MyCapytain.resources.inventory.TextGroup(resource=self.xml.getroot())
            elif work:
                self.type = "work"
                self.log("Work detected")
                self.Text = MyCapytain.resources.inventory.Work(resource=self.xml.getroot())
            else:
                self.log("No metadata type detected (neither work nor textgroup)")
                self.log("Inventory can't be read through Capitains standards")
                yield False

        if self.Text:
            yield True
        else:
            yield False

    def metadata(self):
        status = False
        if self.xml is not None and self.Text:

            if self.type == "textgroup":

                groups = len(self.Text.metadata["groupname"].children)
                self.log("{0} groupname found".format(str(groups)))
                status = groups > 0

            elif self.type == "work":
                status = True
                langs = self.xml.xpath("//ti:translation/@xml:lang", namespaces=TESTUnit.NS)
                if len(langs) != len(self.xml.xpath("//ti:translation", namespaces=TESTUnit.NS)):
                    status = False
                    self.log("Translation(s) are missing lang attribute")

                titles = len(self.Text.metadata["title"].children)
                self.log("{0} titles found".format(titles))
                status = status and titles > 0

                texts = len(self.Text.texts)
                labels = len(
                    [
                        text for text in self.Text.texts.values()
                        if len(text.metadata["label"].children) > 0
                    ]
                )

                self.log("{0}/{1} file(s) with labels".format(labels, texts))
                status = status and labels == texts

                descs = len(
                    [
                        text for text in self.Text.texts.values()
                        if len(text.metadata["description"].children) > 0
                    ]
                )
                self.log("{0}/{1} file(s) with descs".format(descs, texts))
                status = status and labels == descs

        yield status

    def check_urns(self):
        status = False
        if self.xml:
            if self.type == "textgroup":
                urns = [
                    urn
                    for urn in self.xml.xpath("//ti:textgroup/@urn", namespaces=TESTUnit.NS)
                    if urn and len(MyCapytain.common.reference.URN(urn)) == 3
                ]
                self.log("Group urn :" + "".join(self.xml.xpath("//ti:textgroup/@urn", namespaces=TESTUnit.NS)))
                status = len(urns) == 1
            elif self.type == "work":
                worksUrns = [
                        urn
                        for urn in self.xml.xpath("//ti:work/@urn", namespaces=TESTUnit.NS)
                        if urn and len(MyCapytain.common.reference.URN(urn)) == 4
                    ] + [
                        urn
                        for urn in self.xml.xpath("//ti:work/@groupUrn", namespaces=TESTUnit.NS)
                        if urn and len(MyCapytain.common.reference.URN(urn)) == 3
                    ]
                self.log("Group urn : " + "".join(self.xml.xpath("//ti:work/@groupUrn", namespaces=TESTUnit.NS)))
                self.log("Work urn : " + "".join(self.xml.xpath("//ti:work/@urn", namespaces=TESTUnit.NS)))

                texts = self.xml.xpath("//ti:edition|//ti:translation", namespaces=TESTUnit.NS)
                workUrnsText = []

                for text in texts:
                    self.urns.append(text.get("urn"))
                    workUrnsText.append(text.get("workUrn"))

                workUrnsText = [urn for urn in workUrnsText if urn and len(MyCapytain.common.reference.URN(urn)) == 4]
                self.urns = [urn for urn in self.urns if urn and len(MyCapytain.common.reference.URN(urn)) == 5]
                self.log("Editions and translations urns : " + " ".join(self.urns))

                status= len(worksUrns) == 2 and (len(texts)*2)==len(self.urns + workUrnsText)

        yield status

    def test(self):
        """ Test a file with various checks

        :returns: List of urns
        :rtype: list.<str>
        
        """
        self.urns = []

        for test in INVUnit.tests:
            # Show the logs and return the status
            for status in getattr(self, test)():
                yield (INVUnit.readable[test], status, self.logs)
                self.flush()


class CTSUnit(TESTUnit):
    """ CTS testing object

    :param path: Path to the file
    :type path: basestring

    """

    tests = ["parsable", "capitain", "has_urn", "naming_convention", "refsDecl", "passages", "unique_passage", "inventory"]
    readable = {
        "parsable": "File parsing",
        "capitain": "File ingesting in MyCapytain",
        "refsDecl": "RefsDecl parsing",
        "passages": "Passage level parsing",
        "epidoc": "Epidoc DTD validation",
        "tei": "TEI DTD Validation",
        "has_urn": "URN informations",
        "naming_convention": "Naming conventions",
        "inventory": "Available in inventory",
        "unique_passage": "Unique nodes found by XPath"
    }

    def __init__(self, *args, **kwargs):
        super(CTSUnit, self).__init__(*args, **kwargs)
        self.inv = list()
        self.scheme = None

    def capitain(self):
        """ Load the file in MyCapytain
        """
        if self.xml:
            try:
                self.Text = MyCapytain.resources.texts.local.Text(resource=self.xml.getroot())
                yield True
            except XPathEvalError as E:
                self.log("XPath given for citation can't be parsed")
                yield False
            except MyCapytain.errors.RefsDeclError as E:
                self.error(E)
                yield False
            except (IndexError, TypeError) as E:
                self.log("Text can't be read through Capitains standards")
                yield False
        else:
            yield False

    def refsDecl(self):
        """ Contains refsDecl informations
        """
        if self.Text:
            self.log(str(len(self.Text.citation)) + " citation's level found")
            yield len(self.Text.citation) > 0
        else:
            yield False

    def epidoc(self):
        test = subprocess.Popen(
            ["java", "-jar", TESTUnit.JING, TESTUnit.EPIDOC, self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )

        out, error = test.communicate()

        if len(out) > 0:
            for error in TESTUnit.rng_logs(out):
                self.log(error)
        yield len(out) == 0 and len(error) == 0

    def tei(self):
        test = subprocess.Popen(
            ["java", "-jar", TESTUnit.JING, TESTUnit.TEI_ALL, self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False
        )

        out, error = test.communicate()
        if len(out) > 0:
            for error in TESTUnit.rng_logs(out):
                self.log(error)
        yield len(out) == 0 and len(error) == 0

    def passages(self):
        if self.Text:
            for i in range(0, len(self.Text.citation)):
                try:
                    with warnings.catch_warnings(record=True) as w:
                        # Cause all warnings to always be triggered.
                        warnings.simplefilter("always")
                        passages = self.Text.getValidReff(level=i+1)
                        ids = [ref.split(".", i)[-1] for ref in passages]
                        space_in_passage = TESTUnit.FORBIDDEN_CHAR.search("".join(ids))
                        status = len(passages) > 0 and len(w) == 0 and space_in_passage is None
                        self.log(str(len(passages)) + " found")
                        if len(w) > 0:
                            self.log("Duplicate references found : {0}".format(", ".join([str(v.message) for v in w])))
                        if space_in_passage and space_in_passage is not None:
                            self.log("Reference with forbidden characters found: {}".format(
                                " ".join([
                                    "'{}'".format(n)
                                    for ref, n in zip(ids, passages)
                                    if TESTUnit.FORBIDDEN_CHAR.search(ref)
                                ])
                            ))

                        yield status
                except Exception as E:
                    self.error(E)
                    self.log("Error when searching passages at level {0}".format(i+1))
                    yield False
        else:
            yield False

    def unique_passage(self):
        """ Check that citation scheme do not collide
        """
        try:
            # Checking for duplicate
            xpaths = [
                self.Text.xml.xpath(
                    MyCapytain.common.reference.REFERENCE_REPLACER.sub(
                        r"\1",
                        citation.refsDecl
                    ),
                    namespaces=TESTUnit.NS
                )
                for citation in self.Text.citation
            ]
            nodes = [element for xpath in xpaths for element in xpath]
            bad_citation = len(nodes) == len(set(nodes))
            if not bad_citation:
                self.log("Some node are found twice")
                yield False
            else:
                yield True
        except Exception:
            yield False


    def has_urn(self):
        """ Test that a file has its urn saved
        """
        if self.xml is not None:
            if self.scheme == "tei":
                urns = self.xml.xpath("//tei:text[starts-with(@n, 'urn:cts:')]", namespaces=TESTUnit.NS)
            else:
                urns = self.xml.xpath("//tei:body/tei:div[@type='edition' and starts-with(@n, 'urn:cts:')]", namespaces=TESTUnit.NS)
                urns += self.xml.xpath("//tei:body/tei:div[@type='translation' and starts-with(@n, 'urn:cts:')]", namespaces=TESTUnit.NS)
            status = len(urns) > 0
            if status:
                logs = urns[0].get("n")
                try:
                    urn = MyCapytain.common.reference.URN(logs)
                    if len(urn) < 5:
                        status = False
                        self.log("Incomplete URN")
                    elif urn["passage"]:
                        status = False
                        self.log("Reference not accepted in URN")
                except:
                    status = False
                finally:
                    self.log(logs)
                    self.urn = logs
        else:
            status = False
        yield status

    def naming_convention(self):
        """ Check the naming convention of the file
        """
        if self.urn:
            yield self.urn.split(":")[-1] in self.path
        else:
            yield False

    def inventory(self):
        """ Check the naming convention of the file
        """
        if self.urn and self.inv:
            yield self.urn in self.inv
        else:
            yield False

    def test(self, scheme, inventory=None):
        """ Test a file with various checks

        :param scheme: Test with TEI DTD
        :type scheme: str
        :param inventory: URNs to be matched against
        :type inventory: list
        :returns: Iterator containing human readable test name, boolean status and logs
        :rtype: iterator(str, bool, list(str))
        """
        if inventory is not None:
            self.inv = inventory

        tests = [] + CTSUnit.tests
        tests.append(scheme)
        self.scheme = scheme

        for test in tests:
            # Show the logs and return the status
            status = False not in [status for status in getattr(self, test)()]
            yield (CTSUnit.readable[test], status, self.logs)
            self.flush()
