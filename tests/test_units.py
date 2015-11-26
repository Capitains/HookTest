import unittest
import HookTest.units
from lxml import etree

class TestText(unittest.TestCase):
    """ Test the UnitTests for Text
    """
    def setUp(self):
        self.TEI = HookTest.units.CTSUnit("/false/path")
        self.TEI.scheme = "tei"

        self.Epidoc = HookTest.units.CTSUnit("/false/path")
        self.Epidoc.scheme = "epidoc"
    def testUrn(self):
        """ Test the urn Test """
        # When edition
        edition = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="edition" n="{}" /></body></TEI>"""
        # When translation
        translation = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="translation" n="{}" /></body></TEI>"""
        # When wrong because not in main div
        part = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="edition"><div n="{}"/></div></body></TEI>"""
        # When wrong because in wrong div
        main = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div n="{}"/></body></TEI>"""
        # When in Body
        body = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text n="{}"/></TEI>"""

        # Epidoc should fail for TEI
        self.TEI.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False)
        self.TEI.xml = etree.fromstring(translation.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False)
        # Wrong epidoc should be wrong in TEI too
        self.TEI.xml = etree.fromstring(part.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False)
        self.TEI.xml = etree.fromstring(main.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False)
        # Right when TEI
        self.TEI.xml = etree.fromstring(body.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), True, "TEI URN should return True when urn is in text")

        # Epidoc should work with translation and edition
        self.Epidoc.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), True, "div[type='edition'] should work with urn")
        self.Epidoc.xml = etree.fromstring(translation.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), True)
        # Wrong epidoc should be wrong
        self.Epidoc.xml = etree.fromstring(part.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False)
        self.Epidoc.xml = etree.fromstring(main.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False)
        # Wrong when TEI
        self.Epidoc.xml = etree.fromstring(body.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False)

        # Wrong urn should fail with Epidoc or TEI
        self.Epidoc.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False, "Incomplete URN should fail")
        self.Epidoc.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False, "URN with Reference should fail")
        self.TEI.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294"))
        self.assertEqual(self.TEI.has_urn().__next__(), False, "Incomplete URN should fail")
        self.TEI.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2:1.pr"))
        self.assertEqual(self.TEI.has_urn().__next__(), False, "URN with Reference should fail")