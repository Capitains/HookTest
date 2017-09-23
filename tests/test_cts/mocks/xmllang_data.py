from MyCapytain.common.utils import xmlparser
from lxml.etree import tostring

TEMPLATES = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
    <encodingDesc>
      <refsDecl n="CTS">
        <cRefPattern n="chapter" matchPattern="(.+).(.+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div[@type='edition']/tei:div[@n='$1']/tei:div[@n='$2'])"/>
        <cRefPattern n="book" matchPattern="(.+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div[@type='edition']/tei:div[@n='$1'])"/>
      </refsDecl>
    </encodingDesc>
</teiHeader>
<text><body><div></div></body></text>
</TEI>"""
URN = "urn:cts:latinLit:phi1294.phi002.perseus-lat2"
LANG = "lat"

# The following variable is a list of element with error that they should throw and status (XML_OBJECT, STATUS, ERROR)
XMLLANG_DOCUMENTS = [
    ("tei", "<text>", "<text xml:base='{urn}' xml:lang='{lang}'>", True, "TEI works with urn and xml lang on @base/text"),
    ("tei", "<text>", "<text n='{urn}' xml:lang='{lang}'>", False, "TEI fails with urn and xml lang on @n/text"),
    ("tei", "<text>", "<text xml:base='{urn}'>", False, "TEI fails with urn without xml lang on @base/text"),
    ("tei", "<text>", "<text n='{urn}'>", False, "TEI fails with urn without xml lang on @n/text"),

    ("epidoc", "<text>", "<text xml:base='{urn}' xml:lang='{lang}'>", False, "Epidoc fails with urn and xml lang on @base/text"),
    ("epidoc", "<text>", "<text n='{urn}' xml:lang='{lang}'>", False, "Epidoc fails with urn and xml lang on @n/text"),
    ("epidoc", "<text>", "<text xml:base='{urn}'>", False, "Epidoc fails with urn without xml lang on @base/text"),
    ("epidoc", "<text>", "<text n='{urn}'>", False, "Epidoc fails with urn without xml lang on @n/text"),

    ("tei", "<body>", "<body xml:base='{urn}' xml:lang='{lang}'>", False, "TEI fails with urn and xml lang on @base/body"),
    ("tei", "<body>", "<body n='{urn}' xml:lang='{lang}'>", True, "TEI works with urn and xml lang on @n/body"),
    ("tei", "<body>", "<body xml:base='{urn}'>", False, "TEI fails with urn without xml lang on @base/body"),
    ("tei", "<body>", "<body n='{urn}'>", False, "TEI fails with urn without xml lang on @n/body"),

    ("epidoc", "<body>", "<body xml:base='{urn}' xml:lang='{lang}'>", False, "Epidoc fails with urn and xml lang on @base/body"),
    ("epidoc", "<body>", "<body n='{urn}' xml:lang='{lang}'>", False, "Epidoc fails with urn and xml lang on @n/body"),
    ("epidoc", "<body>", "<body xml:base='{urn}'>", False, "Epidoc fails with urn without xml lang on @base/body"),
    ("epidoc", "<body>", "<body n='{urn}'>", False, "Epidoc fails with urn without xml lang on @n/body"),

]
# Epidocs Tests
XMLLANG_DOCUMENTS += [
    (scheme, source, replacement.replace("{epidoc}", type_epidoc), boolean, message.replace("{epidoc}", type_epidoc))
    for scheme, source, replacement, boolean, message in
    [
        ("tei", "<div>", "<div type='{epidoc}' n='{urn}' xml:lang='{lang}'>", False,
         "TEI fails with urn and xml lang on @n/div-{epidoc}"),

        ("tei", "<div>", "<div type='{epidoc}' xml:base='{urn}' xml:lang='{lang}'>", False,
         "TEI fails with urn and xml lang on @xml:base/div-{epidoc}"),

        ("tei", "<div>", "<div type='{epidoc}' xml:base='{urn}' xml:lang='{lang}'>", False,
         "TEI fails with urn and without xml lang on @n/div-{epidoc}"),

        ("tei", "<div>", "<div type='{epidoc}' n='{urn}' xml:lang='{lang}'>", False,
         "TEI fails with urn and without xml lang on @xml:base/div-{epidoc}"),

        ("epidoc", "<div>", "<div type='{epidoc}' n='{urn}' xml:lang='{lang}'>", True,
         "Epidoc works with urn and xml lang on @n/div-{epidoc}"),

        ("epidoc", "<div>", "<div type='{epidoc}' xml:base='{urn}' xml:lang='{lang}'>", False,
         "Epidoc fails with urn and xml lang on @xml:base/div-{epidoc}"),

        ("epidoc", "<div>", "<div type='{epidoc}' xml:base='{urn}'>", False,
         "Epidoc fails with urn and without xml lang on @n/div-{epidoc}"),

        ("epidoc", "<div>", "<div type='{epidoc}' n='{urn}'>", False,
         "Epidoc fails with urn and without xml lang on @xml:base/div-{epidoc}")
    ]
    for type_epidoc in ["edition", "translation", "commentary"]
]
XMLLANG_DOCUMENTS = [
    (
        scheme,
        tostring(xmlparser(TEMPLATES.replace(source, replacement).format(urn=URN, lang=LANG)), encoding=str),
        boolean,
        msg + " ("+replacement.format(urn=URN, lang=LANG)+")"
    )
    for scheme, source, replacement, boolean, msg in XMLLANG_DOCUMENTS
]