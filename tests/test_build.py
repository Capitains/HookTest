import unittest
import mock
import HookTest.build
import HookTest.cmd
from glob import glob
import shutil
import os
import sys
from io import StringIO  # Python3
import tarfile


class TestTravis(unittest.TestCase):
    TESTDIR = 'currentTest/'

    def setUp(self):
        self.perfect_repo = [self.TESTDIR + 'data/stoa0007/__cts__.xml',
                             self.TESTDIR + 'data/stoa0007/stoa002/__cts__.xml',
                             self.TESTDIR + 'data/stoa0007/stoa002/stoa0007.stoa002.opp-lat1.xml',
                             self.TESTDIR + 'data/stoa0040a/__cts__.xml',
                             self.TESTDIR + 'data/stoa0040a/stoa002/__cts__.xml',
                             self.TESTDIR + 'data/stoa0040a/stoa002/stoa0040a.stoa002.opp-lat1.xml',
                             self.TESTDIR + 'data/stoa0040a/stoa003/__cts__.xml',
                             self.TESTDIR + 'data/stoa0040a/stoa003/stoa0040a.stoa003.opp-lat1.xml']
        self.len_perfect_repo = 8
        self.partial_repo = [self.TESTDIR + 'data/stoa0040a/__cts__.xml',
                             self.TESTDIR + 'data/stoa0040a/stoa002/__cts__.xml',
                             self.TESTDIR + 'data/stoa0040a/stoa002/stoa0040a.stoa002.opp-lat1.xml']
        self.len_partial_repo = 3
        self.bad_repo = []
        self.len_bad_repo = 0
        self.tar_contents = self.perfect_repo + ['currentTest/data',
                                                 'currentTest/data/stoa0007',
                                                 'currentTest/data/stoa0007/stoa002',
                                                 'currentTest/data/stoa0040a',
                                                 'currentTest/data/stoa0040a/stoa003',
                                                 'currentTest/data/stoa0040a/stoa002',
                                                 'currentTest/manifest.txt']

    def tearDown(self):
        if os.path.isdir(self.TESTDIR):
            shutil.rmtree(self.TESTDIR)

    def createTestDir(self, d):
        """ Creates directory to test file system actions

        :param d: the source directory to be copied
        :type d: str
        """
        shutil.copytree(d, self.TESTDIR)

    def hooktest_build(self, args):
        """ Run args (Splitted list of command line)

        ..note:: See https://wrongsideofmemphis.wordpress.com/2010/03/01/store-standard-output-on-a-variable-in-python/

        :param args: List of commandline arguments
        :return: Sys stdout, status
        """
        # Store the reference, in case you want to show things again in standard output
        old_stdout = sys.stdout
        # This variable will store everything that is sent to the standard output
        result = StringIO()
        sys.stdout = result
        # Here we can call anything we like, like external modules, and everything
        # that they will send to standard output will be stored on "result"
        status = HookTest.build.cmd(**vars(HookTest.cmd.parse_args_build(args)))
        # Redirect again the std output to screen
        sys.stdout = old_stdout

        # Then, get the stdout like a string and process it!
        result_string = result.getvalue()
        return status, result_string

    def test_init_conditions(self):
        """ Test class initialization """
        a = HookTest.build.Travis("test/path", "test/dest")
        self.assertEqual(a.path, "test/path/", "'path' was incorrectly initialized")
        self.assertEqual(a.dest, "test/dest/", "'dest' was incorrectly initialized")

    def test_args_default(self):
        """ Test to make sure that hooktest-build called with no arguments returns the correct defaults"""
        a = HookTest.cmd.parse_args_build(['./'])
        self.assertEqual(a.path, './', 'Default "path" was not set to current directory.')
        self.assertEqual(a.dest, './', 'Default "dest" was not set to current directory.')
        self.assertEqual(a.travis, False, 'Default "travis" was not set to False')

    def test_terminal_default(self):
        """ Tests to determine if build runs correctly from the command line"""
        self.createTestDir('tests/emptyDir')
        args = ['hooktest-build', self.TESTDIR]
        with mock.patch('sys.argv', args):
            with self.assertRaisesRegex(SystemExit, 'You cannot run build on the base class'):
                HookTest.cmd.cmd_build()

    def test_terminal_travis_no_manifest(self):
        """ Tests if a Travis run from the terminal where there is no manifest.txt in 'path' fails correctly"""
        self.createTestDir('tests/emptyDir')
        args = ['hooktest-build', self.TESTDIR, '--travis']
        with mock.patch('sys.argv', args):
            with self.assertRaisesRegex(SystemExit, 'There is no manifest.txt file to load.\nStopping build.'):
                HookTest.cmd.cmd_build()

    def test_no_manifest(self):
        """ tests to make sure an error is raised and the build is stopped if there is no manifest.txt in 'path'"""
        self.createTestDir('tests/emptyDir')
        status, message = HookTest.build.Travis(path=self.TESTDIR, dest='./').run()
        self.assertFalse(status)
        self.assertEqual(message, 'There is no manifest.txt file to load.\nStopping build.')

    def test_empty_manifest(self):
        """ tests to make sure that when there are no passing files in the manifest.txt that the build exits"""
        self.createTestDir('tests/emptyManifest')
        # Tests with a completely empty manifest.txt file, i.e., no whitespace, no line breaks
        status, message = HookTest.build.Travis(path=self.TESTDIR, dest='./').run()
        self.assertFalse(status)
        self.assertEqual(message, 'The manifest file is empty.\nStopping build.')


    def test_whitespace_manifest(self):
        # Tests with a manifest.txt file that has whitespace and line breaks"""
        self.createTestDir('tests/whitespaceManifest')
        status, message = HookTest.build.Travis(path=self.TESTDIR, dest='./').run()
        self.assertFalse(status)
        self.assertEqual(message, 'The manifest file is empty.\nStopping build.')

    def test_repo_file_list(self):
        """ Tests to make sure that all XML files from a repo are added to the file list for comparison with the manifest"""
        self.createTestDir('tests/100PercentRepo')
        file_list = HookTest.build.Travis(path=self.TESTDIR, dest='./').repo_file_list()
        self.assertCountEqual(file_list, self.perfect_repo, "List of existing XML files in 'path' is incorrect")
        self.assertEqual(len(file_list), self.len_perfect_repo, "The number of XML files in 'path' is incorrect.")

    def test_copy_passing_all(self):
        """ Tests to make sure all files are copied from a 100% passing repository"""
        # Test when 'path' and 'dest' are different
        self.createTestDir('tests/100PercentRepo')
        passing_files = [x.replace(self.TESTDIR, '') for x in self.perfect_repo]
        HookTest.build.Travis(path=self.TESTDIR,
                              dest=self.TESTDIR + 'build').remove_failing(self.perfect_repo, passing_files)
        real = glob(self.TESTDIR + 'build/data/*/*.xml')
        real += glob(self.TESTDIR + 'build/data/*/*/*.xml')
        real = [x.replace(self.TESTDIR + 'build/', '') for x in real]
        self.assertCountEqual(real, passing_files, "The files copied for the build do not match the expected value.")
        self.assertEqual(len(real), self.len_perfect_repo, "The number of files copied for the build is incorrect.")

    def test_copy_passing_some(self):
        """ Tests to make sure only the passing files are copied from a partially passing repository"""
        # Test when 'path' and 'dest' are different
        self.createTestDir('tests/50PercentRepo')
        passing_files = [x.replace(self.TESTDIR, '') for x in self.partial_repo]
        HookTest.build.Travis(path=self.TESTDIR,
                              dest=self.TESTDIR + 'build').remove_failing(self.perfect_repo, passing_files)
        real = glob(self.TESTDIR + 'build/data/*/*.xml')
        real += glob(self.TESTDIR + 'build/data/*/*/*.xml')
        real = [x.replace(self.TESTDIR + 'build/', '') for x in real]
        self.assertCountEqual(real, passing_files, "The files copied for the build do not match the expected value.")
        self.assertEqual(len(real), self.len_partial_repo, "The number of files copied for the build is incorrect.")

    def test_copy_passing_none(self):
        """ Tests to make sure no files are copied from a fully failing repository"""
        # Test when 'path' and 'dest' are different
        self.createTestDir('tests/0PercentRepo')
        passing_files = [x.replace(self.TESTDIR, '') for x in self.bad_repo]
        HookTest.build.Travis(path=self.TESTDIR,
                              dest=self.TESTDIR + '/build').remove_failing(self.perfect_repo, passing_files)
        real = glob(self.TESTDIR + '/build/data/*/*.xml')
        real += glob(self.TESTDIR + '/build/data/*/*/*.xml')
        real = [x.replace(self.TESTDIR + '/build', '') for x in real]
        self.assertCountEqual(real, passing_files, "The files copied for the build do not match the expected value.")
        self.assertEqual(len(real), self.len_bad_repo, "The number of files copied for the build is incorrect.")

    def test_remove_failing_none(self):
        """ Tests to make sure no files are deleted from a 100% passing repository"""
        # Test when 'path' and 'dest' are the same
        self.createTestDir('tests/100PercentRepo')
        passing_files = [x.replace(self.TESTDIR, '') for x in self.perfect_repo]
        HookTest.build.Travis(path=self.TESTDIR,
                              dest=self.TESTDIR).remove_failing(self.perfect_repo, passing_files)
        real = glob(self.TESTDIR + 'data/*/*.xml')
        real += glob(self.TESTDIR + 'data/*/*/*.xml')
        real = [x.replace(self.TESTDIR, '') for x in real]
        self.assertCountEqual(real, passing_files, "The files copied for the build do not match the expected value.")
        self.assertEqual(len(real), self.len_perfect_repo, "The number of files copied for the build is incorrect.")

    def test_remove_failing_some(self):
        """ Tests to make sure all of the failing files are deleted from a partially passing repository"""
        # Test when 'path' and 'dest' are the same
        self.createTestDir('tests/50PercentRepo')
        passing_files = [x.replace(self.TESTDIR, '') for x in self.partial_repo]
        HookTest.build.Travis(path=self.TESTDIR,
                              dest=self.TESTDIR).remove_failing(self.perfect_repo, passing_files)
        real = glob(self.TESTDIR + 'data/*/*.xml')
        real += glob(self.TESTDIR + 'data/*/*/*.xml')
        real = [x.replace(self.TESTDIR, '') for x in real]
        self.assertCountEqual(real, passing_files, "The files copied for the build do not match the expected value.")
        self.assertEqual(len(real), self.len_partial_repo, "The number of files copied for the build is incorrect.")

    def test_remove_failing_all(self):
        """ Tests to make sure all files are deleted from a fully failing repository"""
        # Test when 'path' and 'dest' are the same
        self.createTestDir('tests/0PercentRepo')
        passing_files = [x.replace(self.TESTDIR, '') for x in self.bad_repo]
        HookTest.build.Travis(path=self.TESTDIR,
                              dest=self.TESTDIR).remove_failing(self.perfect_repo, passing_files)
        real = glob(self.TESTDIR + '/data/*/*.xml')
        real += glob(self.TESTDIR + '/data/*/*/*.xml')
        real = [x.replace(self.TESTDIR, '') for x in real]
        self.assertCountEqual(real, passing_files, "The files copied for the build do not match the expected value.")
        self.assertEqual(len(real), self.len_bad_repo, "The number of files copied for the build is incorrect.")

    def test_tar_contents(self):
        """ Compares the contents of the release.tar.gz file produced to the expected contents"""
        self.createTestDir('tests/100PercentRepo')
        HookTest.build.Travis(path=self.TESTDIR, dest=self.TESTDIR).run()
        with tarfile.open(self.TESTDIR + 'release.tar.gz', mode='r:gz') as f:
            self.assertCountEqual(f.getnames(), self.tar_contents)

    def test_base_class(self):
        """ Tests to make sure a build run on the base class returns and error"""
        self.createTestDir('tests/emptyDir')
        with self.assertRaisesRegex(NotImplementedError, 'run is not implemented on the base class'):
            HookTest.build.Build(path=self.TESTDIR, dest='./').run()

    def test_build_cmd(self):
        """ Tests to make sure build.cmd receives kwargs correctly and runs the correct sub-class"""
        self.createTestDir('tests/emptyDir')
        status, message = HookTest.build.cmd(**vars(HookTest.cmd.parse_args_build([self.TESTDIR,
                                                                                   '--dest', self.TESTDIR,
                                                                                   '--travis'])))
        self.assertFalse(status)
        self.assertEqual(message, 'There is no manifest.txt file to load.\nStopping build.')
