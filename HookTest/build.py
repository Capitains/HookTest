import os
from glob import glob
import sys
import tarfile
import shutil
import os


class Build(object):
    """

    :param path: the path to the directory that contains the corpus's data directory
    :type path: str
    :param dest: the folder in which to save the cleaned corpus
    :type dest: str
    """

    def __init__(self, path, dest):

        if path.endswith('/'):
            self.path = path
        else:
            self.path = path + '/'
        if dest.endswith('/'):
            self.dest = dest
        else:
            self.dest = dest + '/'

    def repo_file_list(self):
        """ Build the list of XML files for the source repo represented by self.path

        :return: List of the XML file in the repo
        :rtype: [str]
        """
        files = glob('{}data/*/*/*.xml'.format(self.path))
        files += glob('{}data/*/*.xml'.format(self.path))
        return files

    def remove_failing(self, files, passing):
        """ Remove the failing files from the repository"""
        # Covers the case where source and destination directories are the same, i.e., the changes should be made in place
        if self.path == self.dest:
            for file in files:
                if file.replace(self.path, '') not in passing:
                    os.remove(file)
            dirs = [x for x in glob('{}data/*/*'.format(self.dest)) if os.path.isdir(x)]
            for d in dirs:
                try:
                    os.removedirs(d)
                except OSError:
                    continue
        # Covers the case where the source and destination directories are different, so files are copied instead of removed
        else:
            try:
                shutil.rmtree('{}data'.format(self.dest))
            except:
                pass
            for file in files:
                if file.replace(self.path, '') in passing:
                    try:
                        shutil.copy2(file, file.replace(self.path, self.dest))
                    except FileNotFoundError:
                        os.makedirs(os.path.dirname(file.replace(self.path, self.dest)))
                        shutil.copy2(file, file.replace(self.path, self.dest))

    def run(self):
        """ creates a new corpus directory containing only the passing text files and their metadata files
        """
        raise NotImplementedError('run is not implemented on the base class')


class Travis(Build):
    """ The Travis sub-class is designed to work in a CI system where the files are only temporarily pulled from a
    remote repository. Therefore, it defaults to reading from and writing to ./, actually deleting the files in place.
    If these defaults do not conform to your use case, use the base class instead.

    """

    def run(self):
        try:
            with open('{}manifest.txt'.format(self.path)) as f:
                passing = f.read().split('\n')
        except FileNotFoundError:
            return False, 'There is no manifest.txt file to load.\nStopping build.'
        passing = [x for x in passing if x.strip() != '']
        if len(passing) == 0:
            return False, 'The manifest file is empty.\nStopping build.'
        self.remove_failing(self.repo_file_list(), passing)
        to_zip = [x for x in glob('{}*'.format(self.dest))]
        with tarfile.open("{}release.tar.gz".format(self.dest), mode="w:gz") as f:
            for file in sorted(to_zip):
                f.add(file)
        return True, 'Build successful.'


def cmd(**kwargs):
    """

    :param kwargs: Named arguments
    :type kwargs: dict
    :return:
    :rtype:
    """
    if kwargs['travis'] is True:
        status, message = Travis(path=kwargs['path'], dest=kwargs['dest']).run()
        return status, message
    else:
        return False, 'You cannot run build on the base class'