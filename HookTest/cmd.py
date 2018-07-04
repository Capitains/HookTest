import argparse
import sys
import HookTest.test
import HookTest.build
import os


SCHEMES = {
    "tei": "Use the most recent TEI-ALL DTD",
    "epidoc": "Use the most recent epiDoc DTD",
    "ignore": "Perform no schema validation",
    "auto": "Automatically detect the RNG to use from the xml-model declaration in each individual XML file"
}


def check_schema(schema):
    if schema in SCHEMES:
        return schema
    elif os.path.isfile(schema):
        return ['local_file', schema]
    else:
        raise argparse.ArgumentTypeError('--scheme must either point to an existing local RNG file or be one of the following:\n {}'.format(
            '\n'.join([': '.join([k, v]) for k, v in SCHEMES.items()])
        ))


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

    parser.add_argument('-w', "--workers", type=int, help='Number of workers (processes) to be used', default=1)

    parser.add_argument('-s', "--scheme",
                        help="Scheme to test. 'ignore' test will ignore RNG.",
                        default="auto",
                        type=check_schema)

    parser.add_argument("-v", "--verbose", help="""Verbose Level\n
    - 0\t(Default) Only show necessary Information\n
    - 5\tShow duplicate or forbidden characters (table mode only a the moment\n
    - 7\tAll of before + show failing units (Table Mode only at the moment)\n
    - 10\tAll available details""", default=0, type=int, nargs="?", choices=(0, 5, 7, 10))
    parser.add_argument("-j", "--json", help="Save to specified json file the results", default=None)
    parser.add_argument(
        "-f", "--filter", dest="finder",
        help="Filter using the last part of the URN (eg. tlg0001.tlg001, tlg0001"
        ", tlg0001.tlg001.p-grc1 for urn:cts:greekLit:tlg0001.tlg001.p-grc1",
        default=None
    )
    parser.add_argument(
        "--countwords",
        help="Count words in texts passing the tests",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--console", help="Console Mode",
        default=False, action="store", const="true",
        # Allows for retro-compatibility with older code base
        nargs="?"
    )
    parser.add_argument(
        "--manifest", dest="build_manifest", help="Produce a Manifest", action="store_true", default=False
    )
    parser.add_argument(
        "--allowfailure", help="Returns a passing test result as long as at least one text passes.", action="store_true", default=False
    )
    parser.add_argument(
        "--timeout",
        help="Maximum time to be used on RelaxNG tests. If exceeded, test fails", type=int, default=30
    )

    parser.add_argument(
        "--hookUI", dest="from_travis_to_hook",
        help="Send results to a Hook UI endpoint",
        default=False
    )

    parser.add_argument(
        "--guidelines", help="The version and type of guidelines to use",
        choices=("2.tei", "2.epidoc")
    )

    args = parser.parse_args(args)
    if args.finder:
        args.finderoptions = {"include": args.finder}
        args.finder = HookTest.test.FilterFinder
    if args.console == "inline":
        print("WARNING ! Inline printing is not available anymore since 1.1.8")
        args.console = True
    elif args.console == "table":
        print("Since 1.1.8, you do not need to specify --console table anymore. --console is enough")
    elif args.console:
        args.console = True
    if args.verbose is None:
        args.verbose = 10
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
    parser.add_argument("--travis", help="Run build on Travis or similar CI environment", action="store_true",
                        default=False)
    parser.add_argument("--tar", help="Build a tar archive of the passing files", action="store_true", default=False)
    parser.add_argument("--txt", help="Extract plain text files from the XML files", action="store_true", default=False)
    parser.add_argument("--cites", help="Include citation for each passage in the plain text files",
                        action="store_true", default=False)
    parser.add_argument(
        "--workers",
        help="The number of processes to use for extracting plain text.",
        default=3
    )

    arguments = parser.parse_args(args)

    return arguments


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
