import argparse
import sys
import HookTest.test


def cmd():
    """ Run locally the software
    """
    parser = argparse.ArgumentParser(
        prog='HookTest-Local',
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
    parser.add_argument(
        "-p",
        "--ping",
        help="Send results to a server",
        default=None
    )

    args = parser.parse_args()
    status = HookTest.test.cmd(console=True, **vars(args))
    if status is False:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    cmd()
