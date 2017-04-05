import argparse
import sys
import HookTest.test
import HookTest.build


def parse_args(args):
    """ Parsing function. Written to support unit test

    :param args: List of command line argument
    :return: Parsed argument
    """
    parser = argparse.ArgumentParser(
        prog='hooktest',
        description=" HookTest provides local and easy to use tests for CTS resources package"
    )

    parser.add_argument("path", help="Path containing the repository")

    parser.add_argument(
        "-i",
        "--uuid",
        help="Identifier for a test. This will be used as a temporary folder name",
        default=None
    )
    parser.add_argument("-r", "--repository", help="Name of the git repository", default=None)
    parser.add_argument("-b", "--branch", help="Reference for the branch", default=None)

    parser.add_argument('-w', "--workers", type=int, help='Number of workers to be used', default=1)
    parser.add_argument('-s', "--scheme", help="'tei' or 'epidoc' scheme to be used", default="tei")
    parser.add_argument("-v", "--verbose", help="Show RNG's errors", action="store_true")
    parser.add_argument("-j", "--json", help="Save to specified json file the results", default=None)
    parser.add_argument("-f", "--finder", help="Filter using the last part of the URN (eg. tlg0001.tlg001, tlg0001"
                                               ", tlg0001.tlg001.p-grc1 for urn:cts:greekLit:tlg0001.tlg001.p-grc1",
                        default=None)
    parser.add_argument("--countwords", help="Count words in texts passing the tests", action="store_true", default=None)
    parser.add_argument(
        "-c", "--console", help="Print to console", action="store_true", default=False)
    parser.add_argument('--console_mode', help='Format of console output', choices=['table', 'line'], default='line')
    parser.add_argument("--travis", help="Produce Travis output", action="store_true", default=False)
    parser.add_argument(
        "-p",
        "--ping",
        help="Send results to a server",
        default=None
    )
    parser.add_argument("--allowfailure",
                        help="Returns a passing test result as long as at least one text passes.",
                        action="store_true", default=False)

    args = parser.parse_args(args)
    if args.finder:
        args.finderoptions = {"include": args.finder}
        args.finder = HookTest.test.FilterFinder
    return args


def cmd():
    """ Run locally the software. Should not be called outside of a python cmd.py call
    """
    status = HookTest.test.cmd(**vars(parse_args(sys.argv[1:])))
    if status != HookTest.test.Test.SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)


def parse_args_build(args):
    """ Parsing function. Written to support unit test

    :param args: List of command line argument
    :return: Parsed argument
    """
    parser = argparse.ArgumentParser(
        prog='hooktest-build',
        description=" Builds a repository for release based on the results of HookTest"
    )

    parser.add_argument("path", help="Path containing the repository", default='./')

    parser.add_argument(
        "-d",
        "--dest",
        help="The folder in which the corpus without the failing files should be saved",
        default='./'
    )
    parser.add_argument("--travis", help="Run build on Travis or similar CI environment", action="store_true", default=False)

    args = parser.parse_args(args)
    return args


def cmd_build():
    """ Run locally the software. Should not be called outside of a python cmd.py call
    """
    status, message = HookTest.build.cmd(**vars(parse_args_build(sys.argv[1:])))
    if status is True:
        sys.exit(0)
    else:
        sys.exit(message)

if __name__ == '__main__':
    cmd()
