from unittest import TestCase
from HookTest.test import FilterFinder, Test, FolderFinder
import os.path


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


class TestFolderFinders(TestCase):
    def test_base_repo_folder(self):
        texts, metadata = (FolderFinder(include='./', metadata_names='__capitains__.xml')).find('tests/guidelines_3.0_repo')
        self.assertEqual(len(texts), 15, "There should be 15 texts in the whole repository.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0004a/fulda_dronke.dronke0004a.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0041/fulda_dronke.dronke0041.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0064/fulda_dronke.dronke0064.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0124/fulda_dronke.dronke0124.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0126/fulda_dronke.dronke0126.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0192/fulda_dronke.dronke0192.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0323/fulda_dronke.dronke0323.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0616/fulda_dronke.dronke0616.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat005.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0083/passau.heuwieser0083.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0083/passau.heuwieser0083.lat002.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/./fulda_dronke/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0004a/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0041/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0064/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0124/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0126/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0192/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0323/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0616/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./passau/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./passau/heuwieser0083/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./collected/__capitains__.xml']
        )

    def test_repo_relative_sub_folder(self):
        texts, metadata = (FolderFinder(include='passau', metadata_names='__capitains__.xml')).find('tests/guidelines_3.0_repo')
        self.assertEqual(len(texts), 7, "There should be 7 texts in passau.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat002.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0083/__capitains__.xml']
        )

    def test_repo_absolute_sub_folder(self):
        texts, metadata = (FolderFinder(include=os.path.abspath('tests/guidelines_3.0_repo/data/passau'),
                                        metadata_names='__capitains__.xml')).find('tests/guidelines_3.0_repo')
        self.assertEqual(len(texts), 7,
                         "There should be 7 texts in {}.".format(os.path.abspath('tests/guidelines_3.0_repo/data/passau')))
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat002.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0083/__capitains__.xml']
        )

    def test_repo_relative_sub_sub_folder(self):
        texts, metadata = (FolderFinder(include='passau/heuwieser0073',
                                        metadata_names='__capitains__.xml')).find('tests/guidelines_3.0_repo')
        self.assertEqual(len(texts), 5, "There should be 5 texts in passau/heuwieser0073.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml']
        )

    def test_repo_relative_specific_text(self):
        texts, metadata = (FolderFinder(include='passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                                        metadata_names='__capitains__.xml')).find('tests/guidelines_3.0_repo')
        self.assertEqual(len(texts), 1,
                         "There should be 1 text in passau/heuwieser0073/passau.heuwieser0073.lat001.xml.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml']
        )


class TestFolderFindersInContext(TestCase):
    def test_base_repo_folder(self):
        texts, metadata = Test("tests/guidelines_3.0_repo",
                               finder=FolderFinder,
                               finderoptions={"include": "./"},
                               guidelines='3.epidoc').find()
        self.assertEqual(len(texts), 15, "There should be 15 texts in the whole repository.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0004a/fulda_dronke.dronke0004a.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0041/fulda_dronke.dronke0041.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0064/fulda_dronke.dronke0064.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0124/fulda_dronke.dronke0124.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0126/fulda_dronke.dronke0126.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0192/fulda_dronke.dronke0192.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0323/fulda_dronke.dronke0323.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0616/fulda_dronke.dronke0616.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/passau.heuwieser0073.lat005.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0083/passau.heuwieser0083.lat001.xml',
                    'tests/guidelines_3.0_repo/data/./passau/heuwieser0083/passau.heuwieser0083.lat002.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/./fulda_dronke/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0004a/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0041/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0064/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0124/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0126/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0192/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0323/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./fulda_dronke/dronke0616/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./passau/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./passau/heuwieser0073/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./passau/heuwieser0083/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/./collected/__capitains__.xml']
        )

    def test_repo_relative_sub_folder(self):
        texts, metadata = Test("tests/guidelines_3.0_repo",
                               finder=FolderFinder,
                               finderoptions={"include": "passau"},
                               guidelines='3.epidoc').find()
        self.assertEqual(len(texts), 7, "There should be 7 texts in passau.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat002.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0083/__capitains__.xml']
        )

    def test_repo_absolute_sub_folder(self):
        texts, metadata = Test("tests/guidelines_3.0_repo",
                               finder=FolderFinder,
                               finderoptions={"include": os.path.abspath('tests/guidelines_3.0_repo/data/passau')},
                               guidelines='3.epidoc').find()
        self.assertEqual(len(texts), 7,
                         "There should be 7 texts in {}.".format(os.path.abspath('tests/guidelines_3.0_repo/data/passau')))
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0083/passau.heuwieser0083.lat002.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml',
                       'tests/guidelines_3.0_repo/data/passau/heuwieser0083/__capitains__.xml']
        )

    def test_repo_relative_sub_sub_folder(self):
        texts, metadata = Test("tests/guidelines_3.0_repo",
                               finder=FolderFinder,
                               finderoptions={"include": 'passau/heuwieser0073'},
                               guidelines='3.epidoc').find()
        self.assertEqual(len(texts), 5, "There should be 5 texts in passau/heuwieser0073.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat002.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat003.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat004.xml',
                    'tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml']
        )

    def test_repo_relative_specific_text(self):
        texts, metadata = Test("tests/guidelines_3.0_repo",
                               finder=FolderFinder,
                               finderoptions={"include": 'passau/heuwieser0073/passau.heuwieser0073.lat001.xml'},
                               guidelines='3.epidoc').find()
        self.assertEqual(len(texts), 1,
                         "There should be 1 text in passau/heuwieser0073/passau.heuwieser0073.lat001.xml.")
        self.assertCountEqual(
            texts, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/passau.heuwieser0073.lat001.xml'])
        self.assertCountEqual(
            metadata, ['tests/guidelines_3.0_repo/data/passau/heuwieser0073/__capitains__.xml']
        )
