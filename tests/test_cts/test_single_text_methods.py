import unittest
import HookTest.capitains_units.cts
import HookTest.units
import tests.test_cts.mocks.xmllang_data as CAPITAINS_MOCKS
from lxml import etree

class TestCTS(unittest.TestCase):
    """ Test the UnitTest for __cts__
    """
    pass


class TestText(unittest.TestCase):
    """ Test the UnitTests for Text
    """

    def setUp(self):
        self.backup = [x for x in HookTest.capitains_units.cts.CTSText_TestUnit.tests]

    def tearDown(self):
        HookTest.capitains_units.cts.CTSText_TestUnit.tests = self.backup

    def unit_from_string(self, xml_string, scheme):
        """ Generates a test unit based on xml_string and scheme

        :param xml_string: String representation of the XML Document
        :param scheme: Scheme to apply
        :return: HookTest.capitains_units.cts.CTSText_TestUnit
        """
        node = HookTest.capitains_units.cts.CTSText_TestUnit("/false/path")
        node.scheme = scheme
        node.xml = etree.fromstring(xml_string, HookTest.units.TESTUnit.PARSER)
        return node

    def test_xml_lang(self):
        """ Ensure the XML:LANG test checks against the guideline
        """
        for scheme, xml, status, message in CAPITAINS_MOCKS.XMLLANG_DOCUMENTS:
            unit = self.unit_from_string(xml, scheme)
            results = [result for result in unit.language()]
            self.assertEqual(results[0], status, message)
