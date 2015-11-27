import unittest
import HookTest.units
from lxml import etree

class TestCTS(unittest.TestCase):
    """ Test the UnitTest for __cts__
    """
    def test_lang(self):
        """ Test lang in translation check
        """
        success = """<work xmlns="http://chs.harvard.edu/xmlns/cts">
    <title xml:lang="eng">Div&#257;n</title>
    <edition urn="urn:cts:farsiLit:hafez.divan.perseus-far1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
        </edition>
    <translation  xml:lang="eng" urn="urn:cts:farsiLit:hafez.divan.perseus-eng1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
    </translation>
    <translation  xml:lang="ger" urn="urn:cts:farsiLit:hafez.divan.perseus-ger1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
    </translation>
</work>"""
        fail = """<work xmlns="http://chs.harvard.edu/xmlns/cts">
    <title xml:lang="eng">Div&#257;n</title>
    <edition urn="urn:cts:farsiLit:hafez.divan.perseus-far1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
        </edition>
    <translation  xml:lang="eng" urn="urn:cts:farsiLit:hafez.divan.perseus-eng1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
    </translation>
    <translation urn="urn:cts:farsiLit:hafez.divan.perseus-ger1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
    </translation>
</work>"""
        unit = HookTest.units.INVUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(success))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.metadata().__next__(), True, "When lang, description and edition are there, metadata should work")
        self.assertNotIn(">>>>>> Translation(s) are missing lang attribute", unit.logs)

        unit.xml = etree.ElementTree(etree.fromstring(fail))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.metadata().__next__(), False, "When lang fails, test should fail")
        self.assertIn(">>>>>> Translation(s) are missing lang attribute", unit.logs)



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

    def test_passage_collision(self):
        """ Test collision of passages
        """
        unit = HookTest.units.CTSUnit("tests/passages/test_passage_success.xml")
        parsed = [a for a in unit.parsable()]
        parsed = [a for a in unit.capitain()]
        unit.flush()
        passages = [level for level in unit.passages()]
        self.assertEqual(passages, [True, True, True], "No collision should result in success")

        unit = HookTest.units.CTSUnit("tests/passages/test_passage_fail_1.xml")
        parsed = [a for a in unit.parsable()]
        parsed = [a for a in unit.capitain()]
        unit.flush()
        passages = [level for level in unit.passages()]
        self.assertEqual(passages, [False, False, False], "Collision should result in fail")
        self.assertIn(">>>>>> Duplicate references found : 1", unit.logs)
        self.assertIn(">>>>>> Duplicate references found : 3.1", unit.logs)
        self.assertIn(">>>>>> Duplicate references found : 1.2.1", unit.logs)

    def test_node_collision(self):
        """ Test unique_passage
        """
        frame = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
<encodingDesc>
<refsDecl n="CTS">
    <cRefPattern matchPattern="(\w+).(\w+)" replacementPattern="#xpath({1})">
        <p>This pointer pattern extracts letter and poem</p>
    </cRefPattern>
    <cRefPattern matchPattern="(\w+)" replacementPattern="#xpath({0})">
        <p>This pointer pattern extracts letter</p>
    </cRefPattern>
</refsDecl>
</encodingDesc>
</teiHeader>
<text>
<body>
<div type="edition" n="urn:cts:latinLit:phi1294.phi002.perseus-lat2">
    <div type="chapter" n="1">
        <div type="section" n="1"/>
        <div type="section" n="2"/>
    </div>
    <div type="chapter" n="2">
        <div type="section" n="1"/>
        <div type="section" n="2"/>
    </div>
</div>
</body>
</text>
</TEI>
"""
        unit = HookTest.units.CTSUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(frame.format(
            "/tei:TEI/tei:text/tei:body//tei:div[@n='$1']",
            "/tei:TEI/tei:text/tei:body/tei:div[@n='$1']//tei:div[@n='$2']"
        )))
        ingest = [a for a in unit.capitain()]
        unit.flush()

        results = [result for result in unit.unique_passage()]
        self.assertEqual(results, [False], "Wrong citation with node collision should fail")

        unit.xml = etree.ElementTree(etree.fromstring(frame.format(
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']",
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2']"
        )))
        ingest = [a for a in unit.capitain()]
        unit.flush()
        results = [result for result in unit.unique_passage()]
        self.assertEqual(results, [True], "Right citation with node collision should success")

    def test_illegal_characters(self):
        """ Test unique_passage"""
        frame = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
<encodingDesc>
<refsDecl n="CTS">
    <cRefPattern matchPattern="(\w+).(\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2'])">
        <p>This pointer pattern extracts letter</p>
    </cRefPattern>
    <cRefPattern matchPattern="(\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1'])">
        <p>This pointer pattern extracts letter</p>
    </cRefPattern>
</refsDecl>
</encodingDesc>
</teiHeader>
<text>
<body>
<div type="edition" n="urn:cts:latinLit:phi1294.phi002.perseus-lat2">
    <div n="{0}">
        <div type="section" n="{1}"/>
        <div type="section" n="{2}"/>
        <div type="section" n="{3}"/>
    </div>
    <div n="{4}">
    </div>
</div>
</body>
</text>
</TEI>
    """
        unit = HookTest.units.CTSUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(frame.format(
            "0 1", "a.b", "d-d", "@", "7"
        )))
        ingest = [a for a in unit.capitain()]
        unit.flush()
        results = [result for result in unit.passages()]
        self.assertEqual(results, [False, False], "Illegal character should fail")
        self.assertIn(">>>>>> Reference with forbidden characters found: '0 1.a.b' '0 1.d-d' '0 1.@'", unit.logs)
        self.assertIn(">>>>>> Reference with forbidden characters found: '0 1'", unit.logs)
        unit.xml = etree.ElementTree(etree.fromstring(frame.format(
            0, 1, "q", "b", "105v"
        )))
        ingest = [a for a in unit.capitain()]
        unit.flush()
        results = [result for result in unit.passages()]
        self.assertEqual(results, [True, True], "Legal character should pass")
