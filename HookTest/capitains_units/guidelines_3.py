import re
import warnings
from collections import defaultdict
from os import environ
import os.path
import pkg_resources

import MyCapytain.common
from MyCapytain.common.constants import Mimetypes
from MyCapytain.errors import DuplicateReference, EmptyReference, MissingRefsDecl
from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText

from HookTest.units import TESTUnit
from HookTest.capitains_units.cts import CTSText_TestUnit


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
    ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'cpt': 'http://purl.org/capitains/ns/1.0#'}
    CAPITAINS_RNG = pkg_resources.resource_filename("HookTest", "resources/capitains.rng")

    def __init__(self, *args, timeout=30, **kwargs):
        super(V3Metadata_TestUnit, self).__init__(*args, **kwargs)
        self.timeout = timeout
        self.urns = []
        self.paths = []
        self.dtd_errors = list()
        self.scheme = None

    def capitain(self):
        """ Check that the file conforms to the Capitains RNG
        """
        try:
            if self.scheme == 'auto_rng':
                try:
                    self.Text = self.auto_rng().__next__()
                except FileNotFoundError:
                    self.log('No RNG processing instruction found for {}. Using default capitains.rng instead'.format(self.path))
                    self.Text = self.run_rng(self.CAPITAINS_RNG).__next__()
            else:
                self.Text = self.run_rng(self.CAPITAINS_RNG).__next__()
        except Exception as E:
            self.error(E)

        self.get_ids()
        if self.Text is not False:
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
                    self.paths.append(os.path.normpath(os.path.join(os.path.dirname(self.path), child_path)))
                if child_id is None:
                    try:
                        child_id = child.xpath('cpt:identifier', namespaces=self.ns)[0].text
                    except IndexError:
                        self.log("The identifier for a sub-collection in {} is missing.".format(self.path))
                        continue
                if child.get('readable') == 'true':
                    readable_children.append(child_id)
                else:
                    collection_children.append(child_id)
            self.log("Collection Identifier : " + "".join(collectionId))
            self.log("Sub-collection Identifiers : " + ", ".join(collection_children))
            self.log("Readable Children Identifiers : " + ", ".join(readable_children))

            self.urns = collection_children + readable_children

    def filename(self):
        """ Check to make sure the paths to local files represent actual files
        """
        missing_files = [path for path in self.paths if not os.path.isfile(path)]

        if any(missing_files):
            self.log("The following files were not found: " + ", ".join(missing_files))
            yield False
        else:
            yield True

    def test(self, **kwargs):
        """ Test a file with various checks

        :returns: List of urns
        :rtype: list.<str>

        """
        self.urns = []
        self.scheme = kwargs.get('scheme', None)

        for test in V3Metadata_TestUnit.tests:
            # Show the logs and return the status
            for status in getattr(self, test)():
                yield (V3Metadata_TestUnit.readable[test], status, self.logs)
                self.flush()


class V3Text_TestUnit(CTSText_TestUnit):

    tests = [x for x in CTSText_TestUnit.tests if x != 'naming_convention']

    def language(self):
        """ Tests to make sure an xml:lang element is on the correct node
        """
        if self.guidelines.endswith("epidoc"):
            urns_holding_node = self.xml.xpath(
                "//tei:text/tei:body/tei:div"
                "[@type='edition' or @type='translation' or @type='commentary']"
                "[starts-with(@n, 'urn:cts:')]",
                namespaces=TESTUnit.NS
            )
        elif self.guidelines.endswith("tei"):
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
