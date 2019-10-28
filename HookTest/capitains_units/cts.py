import re
import subprocess
import warnings
from threading import Timer
from collections import defaultdict
from os import makedirs, environ
import os.path
from hashlib import md5
import time
import requests
import shutil
from lxml.etree import parse
import validators

import MyCapytain.common
from MyCapytain.common.constants import Mimetypes
from MyCapytain.errors import DuplicateReference, EmptyReference, MissingRefsDecl
from MyCapytain.resources.collections.cts import XmlCtsTextgroupMetadata, XmlCtsWorkMetadata
from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText

from HookTest.units import TESTUnit


class CTSMetadata_TestUnit(TESTUnit):
    """ CTS testing object

    :param path: Path to the file
    :type path: basestring

    :cvar tests: Contains the list of methods to be run again the text
    :type tests: [str]
    :cvar readable: Human friendly string associated to object methods
    :type readable: dict

    :ivar urns: List of URN retrieved in the file.
    :type urns: [str]
    :ivar type: Type of metadata (textgroup or work)
    :type type: str

    Shared variables with parent class:

    :ivar path: Path for the resource
    :type path: str
    :ivar xml: XML resource, parsed in python. Used to do general checking
    :type xml: lxml._etree.Element

    .. note:: All method in CTSText_TestUnit.tests ("parsable", "capitain", "metadata", "check_urns", "filename" ) yield at \
    least one boolean (might be more) which represents the success of it.
    """

    tests = ["parsable", "capitain", "metadata", "check_urns", "filename"]
    readable = {
        "parsable": "File parsing",
        "capitain": "MyCapytain parsing",
        "metadata": "Metadata availability",
        "check_urns": "URNs testing",
        "filename": "Naming Convention"
    }

    def __init__(self, *args, **kwargs):
        super(CTSMetadata_TestUnit, self).__init__(*args, **kwargs)
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
                Trait = XmlCtsTextgroupMetadata
            elif work:
                self.type = "work"
                self.log("Work detected")
                Trait = XmlCtsWorkMetadata
            else:
                self.log("No metadata type detected (neither work nor textgroup)")
                self.log("Inventory can't be read through Capitains standards")
                yield False

        if self.type in ["textgroup", "work"]:
            try:
                self.Text = Trait.parse(self.xml.getroot())
            except AttributeError as E:
                self.log("Missing URN attribute")
                self.error(E)
            except Exception as E:
                self.error(E)

        if self.Text is not False:
            yield True
        else:
            yield False

    def metadata(self):
        """ Check the presence of all metadata
        """
        status = False
        if self.xml is not None and self.Text is not False:

            if self.type == "textgroup":
                groups = len(self.Text.get_cts_property("groupname"))
                self.log("{0} groupname found".format(str(groups)))
                status = groups > 0

            elif self.type == "work":
                status = True

                # Check that the work has a language
                workLang = self.xml.xpath("//ti:work/@xml:lang", namespaces=TESTUnit.NS)
                if len(workLang) != 1:
                    status = False
                    self.log("Work node is missing its lang attribute")

                langs = self.xml.xpath("//ti:translation/@xml:lang", namespaces=TESTUnit.NS)
                if len(langs) != len(self.xml.xpath("//ti:translation", namespaces=TESTUnit.NS)):
                    status = False
                    self.log("Translation(s) are missing lang attribute")

                com_langs = self.xml.xpath("//ti:commentary/@xml:lang", namespaces=TESTUnit.NS)
                if len(com_langs) != len(self.xml.xpath("//ti:commentary", namespaces=TESTUnit.NS)):
                    status = False
                    self.log("Some Commentaries are missing lang attribute")

                titles = len(self.Text.get_cts_property("title"))
                self.log("{0} titles found".format(titles))
                status = status and titles > 0

                texts = len(self.Text.texts)
                labels = len(
                    [
                        text for text in self.Text.texts.values()
                        if len(text.get_cts_property("label")) > 0
                    ]
                )

                self.log("{0}/{1} file(s) with labels".format(labels, texts))
                status = status and labels == texts

                descs = len(
                    [
                        text for text in self.Text.texts.values()
                        if len(text.get_cts_property("description")) > 0
                    ]
                )
                self.log("{0}/{1} file(s) with descs".format(descs, texts))
                status = status and labels == descs

        yield status

    def check_urns(self):
        """ Check the validity and presence of urns in the text

        .. note:: Populates self.urns
        """
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
                if status:
                    self.urn = urns[0]
            elif self.type == "work":
                matches = True
                onlyOneWork = True
                allMembers = True
                worksUrns = [
                    urn
                    for urn in self.xml.xpath("//ti:work/@urn", namespaces=TESTUnit.NS)
                    if urn and len(MyCapytain.common.reference.URN(urn)) == 4
                ]
                groupUrns = [
                    urn
                    for urn in self.xml.xpath("//ti:work/@groupUrn", namespaces=TESTUnit.NS)
                    if urn and len(MyCapytain.common.reference.URN(urn)) == 3
                ]
                self.urn = None
                urn = None
                if len(worksUrns) == 1:
                    self.urn = worksUrns[0]
                    urn = MyCapytain.common.reference.URN(self.urn)
                    if len(groupUrns) == len(worksUrns):
                        missing = [
                            key for key in ['namespace', 'work', 'textgroup']
                            if getattr(urn, key) is None or len(getattr(urn, key)) == 0
                        ]
                        if missing:
                            self.log("Work URN is missing: {}".format(", ".join(missing)))
                            allMembers = False
                        elif groupUrns[0] != urn.upTo(MyCapytain.common.reference.URN.TEXTGROUP):
                            matches = False
                            self.log("The Work URN is not a child of the Textgroup URN")
                elif len(worksUrns) == 0:
                    self.log("The Work URN on the <ti:work> element is incorrectly formatted or missing.")
                self.log("Group urn : " + "".join(groupUrns))
                self.log("Work urn : " + "".join(worksUrns))

                texts = self.xml.xpath("//ti:edition|//ti:translation|//ti:commentary", namespaces=TESTUnit.NS)

                for text in texts:
                    t_urn = text.get("urn")
                    if t_urn and t_urn.startswith("urn:cts:"):
                        t_urn = MyCapytain.common.reference.URN(t_urn)
                        missing = [
                            key for key in ['namespace', 'work', 'version', 'textgroup']
                            if getattr(t_urn, key) is None or len(getattr(t_urn, key)) == 0
                        ]
                        if missing:
                            self.log("Text {} URN is missing: {}".format(str(t_urn), ", ".join(missing)))
                            allMembers = False
                        elif t_urn.upTo(MyCapytain.common.reference.URN.WORK) != str(urn):
                            matches = False
                            self.log("Text {} does not match parent URN".format(str(t_urn)))
                    self.urns.append(t_urn)
                    worksUrns.append(text.get("workUrn"))

                if len(set(worksUrns)) > 1:
                    onlyOneWork = False
                    self.log("There is different workUrns in the metadata")

                self.urns = [str(urn) for urn in self.urns if urn and len(urn) == 5]

                self.log("Edition, translation, and commentary urns : " + " ".join(self.urns))

                status = allMembers and \
                    matches and onlyOneWork and self.urn and \
                    len(groupUrns) == 1 and \
                    (len(texts) * 2 + 1) == len(self.urns + worksUrns)

        yield status

    def filename(self):
        """ Check the filename and the path correctly represent the path
        """
        status = False
        if self.urn:
            urn = MyCapytain.common.reference.URN(self.urn)
            if self.type == "textgroup":
                status = self.path.endswith("data/{textgroup}/__cts__.xml".format(textgroup=urn.textgroup))
            elif self.type == "work":
                self.log(str(urn))
                status = self.path.endswith("data/{textgroup}/{work}/__cts__.xml".format(
                    textgroup=urn.textgroup, work=urn.work
                ))

        if not status:
            self.log("URN and path does not match")
        yield status

    def test(self):
        """ Test a file with various checks

        :returns: List of urns
        :rtype: list.<str>

        """
        self.urns = []

        for test in CTSMetadata_TestUnit.tests:
            # Show the logs and return the status
            for status in getattr(self, test)():
                yield (CTSMetadata_TestUnit.readable[test], status, self.logs)
                self.flush()


class CTSText_TestUnit(TESTUnit):
    """ CTS testing object

    :param path: Path to the file
    :type path: basestring
    :param countwords: Count the number of words and log it if necessary
    :type countwords: bool

    :cvar tests: Contains the list of methods to be run again the text
    :type tests: [str]
    :cvar readable: Human friendly string associated to object methods
    :type readable: dict

    :ivar inv: List of URN retrieved in metadata. Used to check the availability of metadata for the text
    :type inv: [str]
    :ivar scheme: Scheme to be used to check the
    :type scheme: str
    :ivar Text: Text object according to MyCapytains parsing. Used to find passages
    :type Text: MyCapytain.resources.text.local.Text

    Shared variables with parent class:

    :ivar path: Path for the resource
    :type path: str
    :ivar xml: XML resource, parsed in python. Used to do general checking
    :type xml: lxml._etree.Element

    .. note:: All method in CTSText_TestUnit.tests ( "parsable", "has_urn", "naming_convention", "refsDecl", "passages", \
    "unique_passage", "inventory" ) yield at least one boolean (might be more) which represents the success of it.
    """

    tests = [
        # Parsing the XML
        "parsable",
        # Retrieving the URN (requires parsale
        "has_urn", 'language',
        # Requires has_urn
        "inventory", "naming_convention",
        # Requires parsable
        "refsDecl", "passages", "unique_passage", "duplicate", "forbidden", "empty"
    ]
    breaks = [
        "parsable",
        "refsDecl",
        "passages"
    ]
    readable = {
        "parsable": "File parsing",
        "refsDecl": "RefsDecl parsing",
        "passages": "Passage level parsing",
        "duplicate": "Duplicate passages",
        "forbidden": "Forbidden characters",
        "epidoc": "Epidoc DTD validation",
        "tei": "TEI DTD Validation",
        "auto_rng": "Automatic RNG validation",
        "local_file": "Custom local RNG validation",
        "has_urn": "URN informations",
        "naming_convention": "Naming conventions",
        "inventory": "Available in inventory",
        "unique_passage": "Unique nodes found by XPath",
        "count_words": "Word Counting",
        "language": "Correct xml:lang attribute",
        "empty": "Empty References"
    }
    splitter = re.compile(r'\S+', re.MULTILINE)

    def __init__(self, path, countwords=False, timeout=30, *args, **kwargs):
        self.inv = list()
        self.timeout = timeout
        self.scheme = None
        self.guidelines = None
        self.rng = None
        self.Text = None
        self.xml = None
        self.count = 0
        self.countwords = countwords
        self.citation = list()
        self.duplicates = list()
        self.forbiddens = list()
        self.empties = list()
        self.capitains_errors = list()
        self.test_status = defaultdict(bool)
        self.lang = ''
        self.dtd_errors = list()
        super(CTSText_TestUnit, self).__init__(path, *args, **kwargs)

    def parsable(self):
        """ Chacke that the text is parsable (as XML) and ingest it through MyCapytain then.

        .. note:: Override super(parsable) and add CapiTainS Ingesting to it
        """
        status = next(
            super(CTSText_TestUnit, self).parsable()
        )
        if status is True:
            try:
                self.Text = CapitainsCtsText(resource=self.xml.getroot())
            except MissingRefsDecl as E:
                self.Text = None
                self.log(str(E))
                self.capitains_errors.append(str(E))
                yield False
        else:
            self.Text = None
        yield status

    def refsDecl(self):
        """ Check that the text contains refsDecl informations
        """
        if self.Text:
            # In 1.0.1, MyCapytain actually create an empty citation by default
            if self.Text.citation.is_set():
                self.log(str(len(self.Text.citation)) + " citation's level found")
                yield True
            else:
                yield False
        else:
            yield False

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
        for rng in xml.xpath("/processing-instruction('xml-model')"):
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

    def epidoc(self):
        """ Check the original file against Epidoc rng through a java pipe
        """
        for status in self.run_rng(TESTUnit.EPIDOC):
            yield status

    def tei(self):
        """ Check the original file against TEI rng through a java pipe
        """

        for status in self.run_rng(TESTUnit.TEI_ALL):
            yield status

    def local_file(self):
        """ Check the original file against TEI rng through a java pipe
        """

        for status in self.run_rng(self.rng):
            yield status

    def passages(self):
        """  Check that passages are available at each level. On top of that, it checks for forbidden characters \
        and duplicate in references

        """
        if self.Text and self.Text.citation.refsDecl:
            citations = [c.name for c in self.Text.citation]
            for i in range(0, len(self.Text.citation)):
                try:
                    with warnings.catch_warnings(record=True) as warning_record:
                        # Cause all warnings to always be triggered.
                        warnings.simplefilter("always")
                        passages = self.Text.getValidReff(level=i + 1, _debug=True)
                        ids = [str(ref).split(".", i)[-1] for ref in passages]
                        space_in_passage = TESTUnit.FORBIDDEN_CHAR.search("".join(ids))
                        with_dot = [str(ref) for ref in passages if ref and ref.depth > i + 1]
                        len_passage = len(passages)
                        status = len_passage > 0
                        self.log(str(len_passage) + " found")
                        self.citation.append((i, len_passage, citations[i]))
                        for record in warning_record:
                            if record.category == DuplicateReference:
                                self.duplicates += sorted(str(record.message).split(", "))
                            if record.category == EmptyReference:
                                self.empties += [str(record.message)]
                        if space_in_passage and space_in_passage is not None:
                            self.forbiddens += ["'{}'".format(n)
                                                for ref, n in zip(ids, passages)
                                                if TESTUnit.FORBIDDEN_CHAR.search(ref)]
                        if with_dot and with_dot is not None:
                            self.forbiddens += ["'{}'".format(n) for n in with_dot if "'{}'".format(n) not in self.forbiddens]
                        if status is False:
                            yield status
                            break
                        yield status
                except Exception as E:
                    self.error(E)
                    self.log("Error when searching passages at level {0}".format(i + 1))
                    yield False
                    break
        else:
            yield False

    def duplicate(self):
        """ Detects duplicate references

        """
        if len(self.duplicates) > 0:
            self.log("Duplicate references found : {0}".format(", ".join(self.duplicates)))
            yield False
        elif self.test_status['passages'] is False:
            yield False
        else:
            yield True

    def forbidden(self):
        """ Checks for forbidden characters in references

        """
        if len(self.forbiddens) > 0:
            self.log("Reference with forbidden characters found: {0}".format(", ".join(self.forbiddens)))
            yield False
        elif self.test_status['passages'] is False:
            yield False
        else:
            yield True

    def empty(self):
        """ Detects empty references

        """
        if len(self.empties) > 0:
            self.log("Empty references found : {0}".format(", ".join(self.empties)))
            yield False
        elif self.test_status['passages'] is False:
            yield False
        else:
            yield True

    def unique_passage(self):
        """ Check that citation scheme do not collide (eg. Where text:1 would be the same node as text:1.1)
        """
        try:
            # Checking for duplicate
            xpaths = [
                self.Text.xml.xpath(
                    MyCapytain.common.reference._capitains_cts.REFERENCE_REPLACER.sub(
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
        """ Test that a file has its urn according to CapiTainS Guidelines in its scheme
        """
        if self.xml is not None:
            if self.guidelines == "2.tei":
                urns = self.xml.xpath(
                    "//tei:text/tei:body[starts-with(@n, 'urn:cts:')]",
                    namespaces=TESTUnit.NS)
                urns += self.xml.xpath(
                    "//tei:text[starts-with(@xml:base, 'urn:cts:')]",
                    namespaces=TESTUnit.NS)
            else:
                urns = self.xml.xpath(
                    "//tei:body/tei:div[@type='edition' and starts-with(@n, 'urn:cts:')]",
                    namespaces=TESTUnit.NS
                )
                urns += self.xml.xpath(
                    "//tei:body/tei:div[@type='translation' and starts-with(@n, 'urn:cts:')]",
                    namespaces=TESTUnit.NS
                )
                urns += self.xml.xpath(
                    "//tei:body/tei:div[@type='commentary' and starts-with(@n, 'urn:cts:')]",
                    namespaces=TESTUnit.NS
                )
            status = len(urns) > 0
            if status:
                logs = urns[0].get("n")
                if not logs:
                    logs = urns[0].base
                urn = MyCapytain.common.reference.URN(logs)
                missing_members = [
                    key for key in ['namespace', 'work', 'version', 'textgroup']
                    if getattr(urn, key) is None or len(getattr(urn, key)) == 0
                ]
                if len(urn) < 5:
                    status = False
                    self.log("Incomplete URN")
                elif urn.reference:
                    status = False
                    self.log("Reference not accepted in URN")
                elif len(missing_members) > 0:
                    status = False
                    self.log("Elements of URN are empty: {}".format(", ".join(sorted(missing_members))))
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

    def count_words(self):
        """ Count words in a file
        """
        status = False
        if self.test_status["passages"]:
            text = self.Text.export(Mimetypes.PLAINTEXT, exclude=["tei:note", "tei:teiHeader"])
            self.count = len(type(self).splitter.findall(text))

            self.log("{} has {} words".format(self.urn, self.count))
            status = self.count > 0
        yield status

    def language(self):
        """ Tests to make sure an xml:lang element is on the correct node
        """
        if self.guidelines == "2.epidoc":
            urns_holding_node = self.xml.xpath(
                "//tei:text/tei:body/tei:div"
                "[@type='edition' or @type='translation' or @type='commentary']"
                "[starts-with(@n, 'urn:cts:')]",
                namespaces=TESTUnit.NS
            )
        elif self.guidelines == "2.tei":
            urns_holding_node = self.xml.xpath("//tei:text/tei:body[starts-with(@n, 'urn:cts:')]", namespaces=TESTUnit.NS) + \
                self.xml.xpath("//tei:text[starts-with(@xml:base, 'urn:cts:')]", namespaces=TESTUnit.NS)

        try:
            self.lang = urns_holding_node[0].get('{http://www.w3.org/XML/1998/namespace}lang')
        except IndexError:
            self.lang = ''
        if self.lang == '' or self.lang is None:
            self.lang = 'UNK'
            yield False
        else:
            yield True

    def test(self, scheme, guidelines, rng=None, inventory=None):
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
        tests = [] + CTSText_TestUnit.tests
        if self.countwords:
            tests.append("count_words")

        if scheme in["tei", "epidoc", "auto_rng", "local_file"]:
            tests = [scheme] + tests

        self.scheme = scheme
        self.guidelines = guidelines
        self.rng = rng
        if environ.get("HOOKTEST_DEBUG", False):
            print("Starting %s " % self.path)
        i = 0
        for test in tests:

            # Show the logs and return the status

            if environ.get("HOOKTEST_DEBUG", False):
                print("\t Testing %s " % test)
            status = False not in [status for status in getattr(self, test)()]
            self.test_status[test] = status
            yield (CTSText_TestUnit.readable[test], status, self.logs)
            if test in self.breaks and not status:
                for t in tests[i + 1:]:
                    self.test_status[t] = False
                    yield (CTSText_TestUnit.readable[t], False, [])
                break
            self.flush()
            i += 1
