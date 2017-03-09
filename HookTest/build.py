import os
from glob import glob
import sys


class Build:

    def __init__(self, path, dest):
        """

        :param path: the path to the directory that contains the corpus's data directory
        :type path: str
        :param dest: the folder in which to save the cleaned corpus
        :type dest: str
        """
        self.path = path
        self.dest = dest

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
            with open('manifest.txt'.format(self.path)) as f:
                passing = f.read().split('\n')
        except FileNotFoundError:
            print('There is no manifest.txt file to load.\nStopping build.')
            sys.exit(1)

        files = glob('data/*/*/*.xml'.format(self.path))
        files += glob('data/*/*.xml'.format(self.path))
        for file in files:
            if file not in passing:
                os.remove(file)

        dirs = [x for x in glob('data/*/*') if os.path.isdir(x)]
        for d in dirs:
            try:
                os.removedirs(d)
            except OSError:
                continue


def cmd(**kwargs):
    """

    :param kwargs: Named arguments
    :type kwargs: dict
    :return:
    :rtype:
    """
    print(kwargs)
    if kwargs['travis'] is True:
        Travis(path=kwargs['path'], dest=kwargs['dest'])