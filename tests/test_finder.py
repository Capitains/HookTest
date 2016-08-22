from unittest import TestCase
from HookTest.test import FilterFinder, Test


class TestFilterFinders(TestCase):
    def test_textgroup(self):
        texts, metadata = (FilterFinder(include="stoa0255")).find("tests/repoFilters")
        self.assertEqual(
            len(texts), 11, "There should be 10 texts found in stoa0255"
        )
        self.assertEqual(
            texts, [
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-fre2.xml',
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa006/stoa0255.stoa006.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa007/stoa0255.stoa007.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa008/stoa0255.stoa008.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa009/stoa0255.stoa009.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa010/stoa0255.stoa010.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa011/stoa0255.stoa011.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa012/stoa0255.stoa012.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa013/stoa0255.stoa013.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa014/stoa0255.stoa014.perseus-lat2.xml'
            ],
            "All texts should be found in stoa0255"
        )
        self.assertEqual(
            metadata, [
                'tests/repoFilters/data/stoa0255/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa004/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa006/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa007/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa008/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa009/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa010/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa011/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa012/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa013/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa014/__cts__.xml'
            ],
            "All metadata should be found for textgroup stoa0255"
        )

    def test_work(self):
        texts, metadata = (FilterFinder(include="stoa0255.stoa004")).find("tests/repoFilters")
        self.assertEqual(
            len(texts), 2, "There should be two texts found in stoa0255/stoa004"
        )
        self.assertEqual(
            texts, [
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-fre2.xml',
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-lat2.xml'
            ],
            "All texts should be found in stoa0255/stoa004"
        )
        self.assertEqual(
            metadata, [
                'tests/repoFilters/data/stoa0255/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa004/__cts__.xml'
            ],
            "All metadata should be found for work stoa0255/stoa004"
        )

    def test_version(self):
        texts, metadata = (FilterFinder(include="stoa0255.stoa004.perseus-fre2")).find("tests/repoFilters")
        self.assertEqual(
            len(texts), 1, "There should be one texts found in stoa0255/stoa004/perseus-fre2"
        )
        self.assertEqual(
            texts, [
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-fre2.xml'
            ],
            "One text should be found in stoa0255/stoa004/perseus-fre2"
        )
        self.assertEqual(
            metadata, [
                'tests/repoFilters/data/stoa0255/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa004/__cts__.xml'
            ],
            "All metadata should be found for version stoa0255.stoa004.perseus-fre2"
        )


class TestFilterFindersInContext(TestCase):
    def test_textgroup(self):
        texts, metadata = (
            Test("tests/repoFilters", finder=FilterFinder, finderoptions={"include": "stoa0255"})
        ).find()
        self.assertEqual(
            len(texts), 11, "There should be 10 texts found in stoa0255"
        )
        self.assertEqual(
            texts, [
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-fre2.xml',
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa006/stoa0255.stoa006.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa007/stoa0255.stoa007.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa008/stoa0255.stoa008.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa009/stoa0255.stoa009.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa010/stoa0255.stoa010.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa011/stoa0255.stoa011.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa012/stoa0255.stoa012.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa013/stoa0255.stoa013.perseus-lat2.xml',
                'tests/repoFilters/data/stoa0255/stoa014/stoa0255.stoa014.perseus-lat2.xml'
            ],
            "All texts should be found in stoa0255"
        )
        self.assertEqual(
            metadata, [
                'tests/repoFilters/data/stoa0255/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa004/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa006/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa007/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa008/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa009/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa010/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa011/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa012/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa013/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa014/__cts__.xml'
            ],
            "All metadata should be found for textgroup stoa0255"
        )

    def test_work(self):
        texts, metadata = (
            Test("tests/repoFilters", finder=FilterFinder, finderoptions={"include": "stoa0255.stoa004"})
        ).find()
        self.assertEqual(
            len(texts), 2, "There should be two texts found in stoa0255/stoa004"
        )
        self.assertEqual(
            texts, [
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-fre2.xml',
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-lat2.xml'
            ],
            "All texts should be found in stoa0255/stoa004"
        )
        self.assertEqual(
            metadata, [
                'tests/repoFilters/data/stoa0255/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa004/__cts__.xml'
            ],
            "All metadata should be found for work stoa0255/stoa004"
        )

    def test_version(self):
        texts, metadata = (
            Test("tests/repoFilters", finder=FilterFinder, finderoptions={"include": "stoa0255.stoa004.perseus-fre2"})
        ).find()
        self.assertEqual(
            len(texts), 1, "There should be one texts found in stoa0255/stoa004/perseus-fre2"
        )
        self.assertEqual(
            texts, [
                'tests/repoFilters/data/stoa0255/stoa004/stoa0255.stoa004.perseus-fre2.xml'
            ],
            "One text should be found in stoa0255/stoa004/perseus-fre2"
        )
        self.assertEqual(
            metadata, [
                'tests/repoFilters/data/stoa0255/__cts__.xml',
                'tests/repoFilters/data/stoa0255/stoa004/__cts__.xml'
            ],
            "All metadata should be found for version stoa0255.stoa004.perseus-fre2"
        )