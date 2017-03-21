import unittest
import mock
import HookTest.build
import HookTest.cmd
from glob import glob
import shutil


class TestTravis(unittest.TestCase):
    def setUp(self):
        self.perfect_repo = ['tests/100PercentRepo/data/stoa0007/__cts__.xml',
                             'tests/100PercentRepo/data/stoa0007/stoa002/__cts__.xml',
                             'tests/100PercentRepo/data/stoa0007/stoa002/stoa0007.stoa002.opp-lat1.xml',
                             'tests/100PercentRepo/data/stoa0040a/__cts__.xml',
                             'tests/100PercentRepo/data/stoa0040a/stoa002/__cts__.xml',
                             'tests/100PercentRepo/data/stoa0040a/stoa002/stoa0040a.stoa002.opp-lat1.xml',
                             'tests/100PercentRepo/data/stoa0040a/stoa003/__cts__.xml',
                             'tests/100PercentRepo/data/stoa0040a/stoa003/stoa0040a.stoa003.opp-lat1.xml']

    def test_init_conditions(self):
        """ Try special case of init """
        a = HookTest.build.Travis("test/path", "test/dest")
        self.assertEqual(a.path, "test/path")
        self.assertEqual(a.dest, "test/dest")

    def test_terminal_default(self):
        """ Test to make sure that hooktest-build called with no arguments returns the correct defaults"""
        a = HookTest.cmd.parse_args_build(['./'])
        self.assertEqual(a.path, './')
        self.assertEqual(a.dest, './')
        self.assertEqual(a.travis, False)

    def test_no_manifest(self):
        """ tests to make sure an error is raised and the build is stopped if there is no manifest.txt in 'path'"""
        with self.assertRaisesRegex(SystemExit, 'There is no manifest.txt file to load.\nStopping build.'):
            HookTest.build.Travis(path='tests/emptyDir', dest='./').run()

    def test_empty_manifest(self):
        """ tests to make sure that when there are no passing files in the manifest.txt that the build exits"""
        # Tests with a completely empty manifest.txt file, i.e., no whitespace, no line breaks
        with self.assertRaisesRegex(SystemExit, 'The manifest file is empty.\nStopping build.'):
            HookTest.build.Travis(path='tests/emptyManifest', dest='./').run()
        # Tests with a manifest.txt file that has whitespace and line breaks
        with self.assertRaisesRegex(SystemExit, 'The manifest file is empty.\nStopping build.'):
            HookTest.build.Travis(path='tests/whitespaceManifest', dest='./').run()

    def test_repo_file_list(self):
        """ Tests to make sure that all XML files from a repo are added to the file list for comparison with the manifest"""
        self.assertCountEqual(HookTest.build.Travis(path='tests/100PercentRepo', dest='./').repo_file_list(),
                              self.perfect_repo)

    def test_remove_failing_none(self):
        """ Tests to make sure all failing files are removed from the repository and all passing files remain"""
        # Test when 'path' and 'dest' are different
        passing_files = [x.replace('tests/100PercentRepo', '') for x in self.perfect_repo]
        HookTest.build.Travis(path='tests/100PercentRepo',
                              dest='tests/100PercentRepo/build').remove_failing(self.perfect_repo, passing_files)
        real = glob('tests/100PercentRepo/build/data/*/*.xml')
        real += glob('tests/100PercentRepo/build/data/*/*/*.xml')
        real = [x.replace('tests/100PercentRepo/build', '') for x in real]
        shutil.rmtree('tests/100PercentRepo/build')
        self.assertCountEqual(real, passing_files)