import unittest

import HookTest.capitains_units.cts
import HookTest.units
from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText
from lxml import etree


class TestCTS(unittest.TestCase):
    """ Test the UnitTest for __cts__
    """
    def test_lang(self):
        """ Test lang in translation check
        """
        success = """<work xmlns="http://chs.harvard.edu/xmlns/cts" xml:lang="far" urn="urn:cts:farsiLit:hafez.divan">
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
        success_com = """<work xmlns="http://chs.harvard.edu/xmlns/cts" xml:lang="far" urn="urn:cts:farsiLit:hafez.divan">
    <title xml:lang="eng">Div&#257;n</title>
    <edition urn="urn:cts:farsiLit:hafez.divan.perseus-far1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
        </edition>
    <commentary  xml:lang="ger" urn="urn:cts:farsiLit:hafez.divan.perseus-ger1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
        <about urn="urn:cts:farsiLit:hafez.divan.perseus-far1"/>
    </commentary>
</work>"""
        fail = """<work xmlns="http://chs.harvard.edu/xmlns/cts" urn="urn:cts:farsiLit:hafez.divan">
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
        fail_com = """<work xmlns="http://chs.harvard.edu/xmlns/cts" urn="urn:cts:farsiLit:hafez.divan">
    <title xml:lang="eng">Div&#257;n</title>
    <edition urn="urn:cts:farsiLit:hafez.divan.perseus-far1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
    </edition>
    <commentary urn="urn:cts:farsiLit:hafez.divan.perseus-ger1" workUrn="urn:cts:farsiLit:hafez.divan">
        <label xml:lang="eng">Divan</label>
        <description xml:lang="eng">as</description>
        <about urn="urn:cts:farsiLit:hafez.divan.perseus-far1"/>
    </commentary>
</work>"""
        # test passing translation
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(success))
        [a for a in unit.capitain()]  # We ingest

        unit.flush()
        self.assertEqual(unit.metadata().__next__(), True, "When lang, description and edition are there, metadata should work")
        self.assertNotIn(">>>>>> Translation(s) are missing lang attribute", unit.logs)

        # test passing commentary
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(success_com))
        [a for a in unit.capitain()]  # We ingest

        unit.flush()
        self.assertEqual(unit.metadata().__next__(), True,
                         "When lang, description and edition are there, metadata should work")
        self.assertNotIn(">>>>>> Some Commentaries are missing lang attribute", unit.logs)

        # test failing translation
        unit.xml = etree.ElementTree(etree.fromstring(fail))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.metadata().__next__(), False, "When lang fails, test should fail")
        self.assertIn(">>>>>> Translation(s) are missing lang attribute", unit.logs)

        # test failing commentary
        unit.xml = etree.ElementTree(etree.fromstring(fail_com))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.metadata().__next__(), False, "When lang fails, test should fail")
        self.assertIn(">>>>>> Some Commentaries are missing lang attribute", unit.logs)

    def test_urn(self):
            """ Test URN in translation and commentary check
            """
            success = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="urn:cts:greekLit:tlg2703.tlg001">
  <title xml:lang="lat">Alexias</title>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </edition>
  <translation urn="urn:cts:greekLit:tlg2703.tlg001.opp-lat1" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="eng">Alexias</label>
    <description xml:lang="eng">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </translation>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
  </edition>
</work>"""
            success_com = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="urn:cts:greekLit:tlg2703.tlg001">
  <title xml:lang="lat">Alexias</title>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </edition>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
  </edition>
  <commentary urn="urn:cts:greekLit:tlg2703.tlg001.1st1K-lat1" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="eng">Preface to Alexias</label>
    <description xml:lang="mul">Preface to Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
    <about urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1"/>
  </commentary>
  <commentary urn="urn:cts:greekLit:tlg2703.tlg001.1st1K-lat2" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="mul">Index Nominum et Rerum to Alexias</label>
    <description xml:lang="mul">Index Nominum et Rerum to Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
    <about urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1"/>
  </commentary>
</work>"""
            fail = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="urn:cts:greekLit:tlg2703.tlg001">
  <title xml:lang="lat">Alexias</title>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </edition>
  <translation xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="eng">Alexias</label>
    <description xml:lang="eng">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </translation>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
  </edition>
  <commentary urn="urn:cts:greekLit:tlg2703.tlg001.1st1K-lat1" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="eng">Preface to Alexias</label>
    <description xml:lang="mul">Preface to Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
    <about urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1"/>
  </commentary>
  <commentary urn="urn:cts:greekLit:tlg2703.tlg001.1st1K-lat2" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="mul">Index Nominum et Rerum to Alexias</label>
    <description xml:lang="mul">Index Nominum et Rerum to Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
    <about urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1"/>
  </commentary>
</work>"""
            fail_com = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="urn:cts:greekLit:tlg2703.tlg001">
  <title xml:lang="lat">Alexias</title>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </edition><translation urn="urn:cts:greekLit:tlg2703.tlg001.opp-lat1" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="eng">Alexias</label>
    <description xml:lang="eng">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
  </translation>
  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="lat">Alexias</label>
    <description xml:lang="mul">Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
  </edition>
  <commentary urn="urn:cts:greekLit:tlg2703.tlg001.1st1K-lat1" xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="eng">Preface to Alexias</label>
    <description xml:lang="mul">Preface to Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
    <about urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1"/>
  </commentary>
  <commentary xml:lang="lat" workUrn="urn:cts:greekLit:tlg2703.tlg001">
    <label xml:lang="mul">Index Nominum et Rerum to Alexias</label>
    <description xml:lang="mul">Index Nominum et Rerum to Anna Comnena, Alexias, Reiferscheid, Teubner, 1884</description>
    <about urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc1"/>
  </commentary>
</work>"""
            # test passing translation
            unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("/a/b")
            unit.xml = etree.ElementTree(etree.fromstring(success))
            [a for a in unit.capitain()]  # We ingest

            unit.flush()
            self.assertEqual(unit.check_urns().__next__(), True,
                             "When all URNs are present, check_urn should work")
            self.assertCountEqual(['urn:cts:greekLit:tlg2703.tlg001.opp-grc2',
                                   'urn:cts:greekLit:tlg2703.tlg001.opp-lat1',
                                   'urn:cts:greekLit:tlg2703.tlg001.opp-grc1'],
                                  unit.urns)

            # test passing commentary
            unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("/a/b")
            unit.xml = etree.ElementTree(etree.fromstring(success_com))
            [a for a in unit.capitain()]  # We ingest

            unit.flush()
            self.assertEqual(unit.check_urns().__next__(), True,
                             "When all URNs are present, check_urn should work")
            self.assertCountEqual(['urn:cts:greekLit:tlg2703.tlg001.opp-grc2',
                                   'urn:cts:greekLit:tlg2703.tlg001.opp-grc1',
                                   'urn:cts:greekLit:tlg2703.tlg001.1st1K-lat1',
                                   'urn:cts:greekLit:tlg2703.tlg001.1st1K-lat2'],
                                  unit.urns)

            # test failing translation
            unit.xml = etree.ElementTree(etree.fromstring(fail))
            ingest = [a for a in unit.capitain()]
            unit.capitain()  # We ingest
            unit.flush()
            self.assertEqual(unit.check_urns().__next__(), False, "When lang fails, test should fail")
            self.assertNotIn("urn:cts:greekLit:tlg2703.tlg001.opp-lat1", unit.logs, "Missing URN should not be in logs")

            # test failing commentary
            unit.xml = etree.ElementTree(etree.fromstring(fail_com))
            ingest = [a for a in unit.capitain()]
            unit.capitain()  # We ingest
            unit.flush()
            self.assertEqual(unit.check_urns().__next__(), False, "When lang fails, test should fail")
            self.assertNotIn("urn:cts:greekLit:tlg2703.tlg001.1st1K-lat2", unit.logs, "Missing URN should not be in logs")

    def test_miss_urn_parse(self):
        """ Test lang in translation check
        """
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
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(fail))
        self.assertEqual(
            list(unit.capitain()), [False],
            "Parsing should fail but not raise"
        )

    def test_misformatted_work_urn(self):
        """ test to make sure that a misformatted work URN does not cause a crash and that it returns the correct error
        """
        fail_long = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2">
          <title xml:lang="lat">Alexias</title>
          <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
            <label xml:lang="lat">Alexias</label>
            <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
          </edition>
        </work>"""
        fail_short = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="urn:cts:greekLit:tlg2703">
                  <title xml:lang="lat">Alexias</title>
                  <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
                    <label xml:lang="lat">Alexias</label>
                    <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
                  </edition>
                </work>"""
        fail_missing = """<work xmlns="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:tlg2703" xml:lang="grc" urn="">
                          <title xml:lang="lat">Alexias</title>
                          <edition urn="urn:cts:greekLit:tlg2703.tlg001.opp-grc2" xml:lang="grc" workUrn="urn:cts:greekLit:tlg2703.tlg001">
                            <label xml:lang="lat">Alexias</label>
                            <description xml:lang="mul">Anna Comnena, Alexias, Scopenus, Weber, 1839</description>
                          </edition>
                        </work>"""
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("/a/b")
        # test work URN that is too long
        unit.xml = etree.ElementTree(etree.fromstring(fail_long))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.check_urns().__next__(), False,
                         "Incorrectly formatted work URN should cause test should fail")
        self.assertIn(">>>>>> The Work URN on the <ti:work> element is incorrectly formatted or missing.", unit.logs,
                      "A URN that is too long should add the correct message to the unit.logs.")

        # test work URN that is too short
        unit.xml = etree.ElementTree(etree.fromstring(fail_short))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.check_urns().__next__(), False,
                         "Incorrectly formatted work URN should cause test should fail")
        self.assertIn(">>>>>> The Work URN on the <ti:work> element is incorrectly formatted or missing.", unit.logs,
                      "A URN that is too long should add the correct message to the unit.logs.")

        # test work URN that is missing
        unit.xml = etree.ElementTree(etree.fromstring(fail_missing))
        ingest = [a for a in unit.capitain()]
        unit.capitain()  # We ingest
        unit.flush()
        self.assertEqual(unit.check_urns().__next__(), False,
                         "Incorrectly formatted work URN should cause test should fail")
        self.assertIn(">>>>>> The Work URN on the <ti:work> element is incorrectly formatted or missing.", unit.logs,
                      "A URN that is too long should add the correct message to the unit.logs.")

    def test_capitains_parse(self):
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("./tests/repo2/data/wrongmetadata/__cts__.xml")
        self.assertEqual(
            list(unit.parsable()) + list(unit.capitain()), [True, True],
            "Parsing should work"
        )

    def test_capitains_metadatatextgroup(self):
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("./tests/repo2/data/wrongmetadata/__cts__.xml")
        self.assertEqual(
            list(unit.parsable()) + list(unit.capitain()) + list(unit.metadata()), [True, True, False],
            "No lang in groupname should fail"
        )
        unit = HookTest.capitains_units.cts.CTSMetadata_TestUnit("./tests/repo2/data/tlg2255/__cts__.xml")
        self.assertEqual(
            list(unit.parsable()) + list(unit.capitain()) + list(unit.metadata()), [True, True, True],
            "Lang in groupname should fail"
        )


class TestText(unittest.TestCase):
    """ Test the UnitTests for Text
    """

    def setUp(self):
        self.TEI = HookTest.capitains_units.cts.CTSText_TestUnit("/false/path")
        self.TEI.scheme = "tei"
        self.backup = [x for x in HookTest.capitains_units.cts.CTSText_TestUnit.tests]
        self.Epidoc = HookTest.capitains_units.cts.CTSText_TestUnit("/false/path")
        self.Epidoc.scheme = "epidoc"
        self.frame = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
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
    <div type="chapter" n="{2}">
        <div type="section" n="{3}"/>
        <div type="section" n="{4}"/>
        <div type="section" n="{5}"/>
    </div>
    <div type="chapter" n="{6}">
        <div type="section" n="{7}"/>
        <div type="section" n="{8}"/>
    </div>
</div>
</body>
</text>
</TEI>
"""

    def tearDown(self):
        HookTest.capitains_units.cts.CTSText_TestUnit.tests = list(self.backup)

    def testUrn(self):
        """ Test the urn Test """
        # When edition
        edition = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="edition" n="{}" /></body></TEI>"""
        # When translation
        translation = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="translation" n="{}" /></body></TEI>"""
        # When commentary
        commentary = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="commentary" n="{}" /></body></TEI>"""
        # When wrong because not in main div
        part = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div type="edition"><div n="{}"/></div></body></TEI>"""
        # When wrong because in wrong div
        main = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><body><div n="{}"/></body></TEI>"""
        # When in Body
        body = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text><body n="{}"/></text></TEI>"""
        # When in Body
        xmlbase = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text xml:base="{}"><body/></text></TEI>"""

        # Epidoc should fail for TEI
        self.TEI.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False, "Epidoc should fail for TEI")
        self.TEI.xml = etree.fromstring(translation.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False, "Epidoc should fail for TEI")
        # Wrong epidoc should be wrong in TEI too
        self.TEI.xml = etree.fromstring(part.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False, "Wrong epidoc should be wrong in TEI too")
        self.TEI.xml = etree.fromstring(main.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), False, "Wrong epidoc should be wrong in TEI too")
        # Right when TEI
        self.TEI.xml = etree.fromstring(body.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), True, "TEI URN should return True when urn is in text")
        # Right when TEI with XML:BASE
        self.TEI.xml = etree.fromstring(xmlbase.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.TEI.has_urn().__next__(), True, "TEI URN should return True when urn is in text xmlbase")

        # Epidoc should work with translation and edition
        self.Epidoc.xml = etree.fromstring(edition.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), True, "div[type='edition'] should work with urn")
        self.Epidoc.xml = etree.fromstring(translation.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), True, "Epidoc should work with translation and edition")
        self.Epidoc.xml = etree.fromstring(commentary.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), True, "Epidoc should work with translation and edition")
        # Wrong epidoc should be wrong
        self.Epidoc.xml = etree.fromstring(part.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False, "Wrong epidoc should be wrong")
        self.Epidoc.xml = etree.fromstring(main.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False, "Wrong epidoc should be wrong")
        # Wrong when TEI
        self.Epidoc.xml = etree.fromstring(body.format("urn:cts:latinLit:phi1294.phi002.perseus-lat2"))
        self.assertEqual(self.Epidoc.has_urn().__next__(), False, "Epidoc wrong when using TEI Guidelines")

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
        unit = HookTest.capitains_units.cts.CTSText_TestUnit("tests/passages/test_passage_success.xml")
        parsed = [a for a in unit.parsable()]
        unit.flush()
        results = [result for result in unit.passages()]
        unit.test_status['passages'] = True
        passages = list(unit.duplicate())
        self.assertEqual(passages, [True], "No collision should result in success")

        unit = HookTest.capitains_units.cts.CTSText_TestUnit("tests/passages/test_passage_fail_1.xml")
        parsed = [a for a in unit.parsable()]
        unit.flush()
        results = [result for result in unit.passages()]
        passages = list(unit.duplicate())
        self.assertEqual(passages, [False], "Collision should result in fail")
        self.assertIn(">>>>>> Duplicate references found : 1, 1.2, 1.pr, 3.1, 1.2.1, 1.pr.1, 3.1.1, 3.1.2", unit.logs)

    def test_passage_wrong_refsDecl_middle(self):
        """ Test collision of passages
        """
        unit = HookTest.capitains_units.cts.CTSText_TestUnit("tests/passages/test_passage_fail_second_level.xml")
        parsed = [a for a in unit.parsable()]
        unit.flush()
        results = [result for result in unit.passages()]
        self.assertEqual(results, [True, False], "Wrong refsDecl should stop the test")
        unit.test_status['passages'] = False
        passages = list(unit.duplicate())
        self.assertEqual(passages, [False], "Failing passages should result in duplicate failure")
        passages = list(unit.forbidden())
        self.assertEqual(passages, [False], "Failing passages should result in forbidden failure")

    def test_node_collision(self):
        """ Test unique_passage
        """

        unit = HookTest.capitains_units.cts.CTSText_TestUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(self.frame.format(
            "/tei:TEI/tei:text/tei:body//tei:div[@n='$1']",
            "/tei:TEI/tei:text/tei:body/tei:div[@n='$1']//tei:div[@n='$2']",
            1, 1, 2, 3, 1, 1, 2
        ))).getroot()
        unit.Text = CapitainsCtsText(resource=unit.xml)
        unit.flush()

        results = [result for result in unit.unique_passage()]
        self.assertEqual(results, [False], "Wrong citation with node collision should fail")

        unit.xml = etree.ElementTree(etree.fromstring(self.frame.format(
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']",
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2']",
            1, 1, 2, 3, 1, 1, 2
        ))).getroot()
        unit.Text = CapitainsCtsText(resource=unit.xml)
        unit.flush()
        results = [result for result in unit.unique_passage()]
        self.assertEqual(results, [True], "Right citation with node collision should success")

    def test_illegal_characters_fail(self):
        """ Test that illegal characters are detected"""

        unit = HookTest.capitains_units.cts.CTSText_TestUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(self.frame.format(
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']",
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2']",
            "0 1", "a.b", "d-d", "@", "7", "1", "2"
        ))).getroot()
        unit.Text = CapitainsCtsText(resource=unit.xml)
        unit.flush()
        results = [result for result in unit.passages()]
        self.assertEqual(results, [True, True], "Passages are found")
        results = list(unit.forbidden())
        self.assertEqual(results, [False], "Illegal character should fail")
        self.assertIn(">>>>>> Reference with forbidden characters found: '0 1', '0 1.a.b', '0 1.d-d', '0 1.@'", unit.logs)
        self.assertCountEqual(unit.forbiddens, ["'0 1'", "'0 1.a.b'", "'0 1.d-d'", "'0 1.@'"], "All passage IDs containing forbidden characters should be stored.")

    def test_illegal_characters_pass(self):
        """ Test that forbidden passes when there are no illegal characters"""
        unit = HookTest.capitains_units.cts.CTSText_TestUnit("/a/b")
        unit.xml = etree.ElementTree(etree.fromstring(self.frame.format(
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']",
            "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']/tei:div[@n='$2']",
            0, 1, "q", "b", "105v", "1", "2"
        ))).getroot()
        unit.Text = CapitainsCtsText(resource=unit.xml)
        unit.flush()
        results = [result for result in unit.passages()]
        self.assertEqual(results, [True, True], "Passages are found")
        unit.test_status['passages'] = True
        results = list(unit.forbidden())
        self.assertEqual(results, [True], "Illegal characters should pass if no forbidden characters")
        self.assertEqual(unit.forbiddens, [], "All passage IDs containing forbidden characters should be stored.")

    def test_count_words(self):
        """ Test collision of passages
        """
        unit = HookTest.capitains_units.cts.CTSText_TestUnit("tests/passages/test_passage_success.xml")
        HookTest.capitains_units.cts.CTSText_TestUnit.tests = [
            "parsable", "has_urn", "passages"
        ]
        x = list(unit.test("epidoc"))
        unit.flush()
        a = list(unit.count_words())
        self.assertEqual(
            unit.logs, ['>>>>>> urn:cts:latinLit:phi1294.phi002.perseus-lat2 has 173 words'],
            "Words should be logged"
        )
        self.assertEqual(
            a, [True]
        )

    def test_count_words_fails(self):
        """ Test collision of passages
        """
        unit = HookTest.capitains_units.cts.CTSText_TestUnit("tests/repo2/data/capitainingest/tei2/tlg4089.tlg004.1st1k-grc1.xml")
        HookTest.capitains_units.cts.CTSText_TestUnit.tests = [
            "parsable", "has_urn", "passages"
        ]
        x = list(unit.test("epidoc"))
        unit.flush()
        a = list(unit.count_words())
        self.assertEqual(
            unit.logs, [], "Nothing should be logged"
        )
        self.assertEqual(
            a, [False], "Test should fail"
        )

    def test_run_relaxng(self):
        """ Tests to make sure that an epidoc edition text with an xml:lang attribute on the div[@type="edition"] passes
        """
        unit = HookTest.capitains_units.cts.CTSText_TestUnit("tests/100PercentRepo/data/stoa0007/stoa002/stoa0007.stoa002.opp-lat1.xml")
        unit.xml = etree.parse("tests/100PercentRepo/data/stoa0007/stoa002/stoa0007.stoa002.opp-lat1.xml", HookTest.units.TESTUnit.PARSER)
        unit.scheme = "epidoc"
        unit.flush()
        results = [result for result in unit.epidoc()]
        self.assertEqual(results, [True], "Epidoc RelaxNG should run correctly")