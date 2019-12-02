import re
import warnings
from collections import defaultdict
from os import makedirs, environ
import os.path
from hashlib import md5
import time
import requests
import shutil
from lxml.etree import parse
import validators
import pkg_resources

import MyCapytain.common
from MyCapytain.common.constants import Mimetypes
from MyCapytain.errors import DuplicateReference, EmptyReference, MissingRefsDecl
from MyCapytain.resources.collections.dts import DtsCollection
from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText

from HookTest.units import TESTUnit


class V3Metadata_TestUnit(TESTUnit):
    """ Testing object for MyCapytain Guidelines version 3 metadata objects

    :param path: Path to the file
    :type path: basestring

    :cvar tests: Contains the list of methods to be run again the text
    :type tests: [str]
    :cvar readable: Human friendly string associated to object methods
    :type readable: dict

    :ivar identifiers: List of identifiers retrieved in the file.
    :type identifiers: [str]
    :ivar paths: List of paths to the member collections found in this file
    :type paths: [str]

    Shared variables with parent class:

    :ivar path: Path for the resource
    :type path: str
    :ivar xml: XML resource, parsed in python. Used to do general checking
    :type xml: lxml._etree.Element

    .. note:: All method in V3Metadata_TestUnit.tests ("parsable", "capitain", "metadata", "check_urns", "filename" )
    yield at least one boolean (might be more) which represents the success of it.
    """

    tests = ["parsable", "capitain", "filename"]
    readable = {
        "parsable": "File parsing",
        "capitain": "MyCapytain parsing",
        "filename": "Member files exist"
    }
    ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'cpt': 'http://purl.org/ns/capitains'}
    CAPITAINS_RNG = pkg_resources.resource_filename("HookTest", "resources/capitains.rng")

    def __init__(self, *args, **kwargs):
        super(V3Metadata_TestUnit, self).__init__(*args, **kwargs)
        self.identifiers = []
        self.paths = []

    def capitain(self):
        """ Check that the file conforms to the Capitains RNG
        """
        try:
            self.Text = self.run_rng(self.CAPITAINS_RNG)
        except Exception as E:
            self.error(E)

        if self.Text is not False:
            self.get_ids()
            yield True
        else:
            yield False

    def get_ids(self):
        """ Sends the identifiers found in the file to the logs. Also populates self.identifiers and self.paths

        """
        # This is no longer a test but simply sends what is found to the logs and saves readable children to self.identifiers
        if self.xml:
            collectionId = self.xml.xpath('/cpt:collection/cpt:identifier/text()', namespaces=self.ns)
            readable_children = []
            collection_children = []
            for child in self.xml.xpath('/cpt:collection/cpt:members/cpt:collection', namespaces=self.ns):
                child_path = child.get('path')
                child_id = child.get('identifier')
                if child_path:
                    self.paths.append(os.path.normpath(os.path.join(self.path, child_path)))
                if child_id is None:
                    child_id = child.xpath('cpt:identifier', namespaces=self.ns)[0].text
                if child.get('readable') == 'true':
                    readable_children.append(child_id)
                else:
                    collection_children.append(child_id)
            self.log("Collection Identifier : " + "".join(collectionId))
            self.log("Sub-collection Identifiers : " + ", ".join(collection_children))
            self.log("Readable Children Identifiers : " + ", ".join(readable_children))

            self.identifiers = collection_children + readable_children

    def filename(self):
        """ Check to make sure the paths to local files represent actual files
        """
        missing_files = [path for path in self.paths if not os.path.isfile(path)]

        if any(missing_files):
            self.log("The following files were not found: " + ", ".join(missing_files))
            yield False
        else:
            yield True

    def test(self):
        """ Test a file with various checks

        :returns: List of urns
        :rtype: list.<str>

        """
        self.identifiers = []

        for test in V3Metadata_TestUnit.tests:
            # Show the logs and return the status
            for status in getattr(self, test)():
                yield (V3Metadata_TestUnit.readable[test], status, self.logs)
                self.flush()


class V3Text_TestUnit(TESTUnit):
    """ DTS testing object

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

    .. note:: All method in DTSText_TestUnit.tests ( "parsable", "has_urn", "naming_convention", "refsDecl", "passages", \
    "unique_passage", "inventory" ) yield at least one boolean (might be more) which represents the success of it.
    """

    tests = [
        # Parsing the XML
        "parsable",
        # Retrieving the URN (requires parsale
        "has_urn", 'language',
        # Requires has_urn
        "inventory",  # "naming_convention", Naming conventions test is not appropriate in DTS
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
        # "naming_convention": "Naming conventions",
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
        super(DTSText_TestUnit, self).__init__(path, *args, **kwargs)

    def parsable(self):
        """ Chacke that the text is parsable (as XML) and ingest it through MyCapytain then.

        .. note:: Override super(parsable) and add CapiTainS Ingesting to it
        """
        status = next(
            super(DTSText_TestUnit, self).parsable()
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
        tests = [] + DTSText_TestUnit.tests
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
            yield (DTSText_TestUnit.readable[test], status, self.logs)
            if test in self.breaks and not status:
                for t in tests[i + 1:]:
                    self.test_status[t] = False
                    yield (DTSText_TestUnit.readable[t], False, [])
                break
            self.flush()
            i += 1
