from HookTest.cmd import parse_args
from HookTest.test import cmd
from HookTest.capitains_units.cts import CTSText_TestUnit

unit = CTSText_TestUnit(
    path="../canonical-lat-test/data/phi0978/phi001/phi0978.phi001.perseus-eng1.xml",
    countwords=True, timeout=2
)
for x in unit.test(scheme="epidoc"):
    print(x)

cmd(**vars(parse_args([
    "../canonical-lat-test",
    "-w", "8", "--countword", "--scheme", "epidoc",
    "--allowfailure", "--console", "table", "--verbose", "10"
])))
