import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor

class ChtiShred(Shred):
    tbl_name = "chti"
    create_tbl_sql = \
"""create table chti(
line integer primary key references log(line),
type text, 
req integer,
resp integer,
url text,
crumbthread text,
crumbtime datetime,
stackframe text)"""
    tbl_index_sqls = [
                       ]
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls)

    entry_signature = ' CapturingHttpItem] '
    entry_selector = ShredEntrySelector(entry_signature)

    type_signatures = {
        'beginreq': ['request@', 'BEGIN 20'],
        'beginresp': ['response@', 'BEGIN 20'],
        'endreq': ['request@', 'END & HISTORY:'],
        'endresp': ['response@', ' END & HISTORY:'],
        'endhreq': ['request@', ' END 20'],
        'endhresp': ['response@', ' END & HISTORY:'],
        'framereq': ['request@'],
        'frameresp': ['response@'],
        'contains': '- url @detectLibraryClass',
        'nolib': '- No library found',
        'adopted': 'from orphanage by CodeSource path',
        'used': ' to library usage for lib ',
    }
    entry_classifier = ShredEntryClassifier(type_signatures)
    # entry_classifier = ShredEntryClassifier()   # just one default type

    # extracted_val_names=['req', 'resp', 'url', 'crumbthread', 'crumbtime', 'stackframe']
    # value_extractors = {
    #     # - Not putting java.util.Hashtable$KeySet in orphanage as its from bootstrapped classloade
    #     'noput': re.compile(
    #         r"\- Not putting (?P<fqcn>\S+) in orphanage as its from (?P<location>~NOLOC~)?(?P<application>~NOAPP~)?"),
    #     # - Couldn't find app for org.jboss.Main$ShutdownHook with CodeSource location file:/opt/jboss/bin/run.jar
    #     'noapp': re.compile(
    #         r"\- Couldn't find app for (?P<fqcn>\S+) with CodeSource path (?P<application>~NOAPP~)?(?P<location>.*)$"),
    #     # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
    #     'orphan': re.compile(r"\- Adding (?P<fqcn>\S+) to orphanage(?P<location>~NOLOC~)?(?P<application>~NOAPP~)?$"),
    #     # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
    #     'uninventoried': re.compile(
    #         r"\- Adding (?P<fqcn>\S+) to list of missed classload events for uninventoried (?P<location>~NOLOC~)?(?P<application>.*)$"),
    #     # - url @detectLibraryClass vfs:/opt/jboss/server/default/deploy/jbossweb.sar/jbossweb.jar/ contains org.apache.tomcat.util.buf.C2BConverter for application 'platform-servlet'
    #     'contains': re.compile(
    #         r"\- url \@detectLibraryClass (?P<location>.+) contains (?P<fqcn>\S+) for app \".+\" \((?P<application>.*)\)$"),
    #     'nolib': re.compile(
    #         r"\- No library found for \S+ in app \".+\" (?P<location>~NOLOC~)?(?P<fqcn>~NOCLASS~)?\((?P<application>.*)\)$"),
    #     # - Took {} from orphanage by CodeSource path {} and passing to app {}
    #     'adopted': re.compile(
    #         r"\- Took (?P<fqcn>\S+) from orphanage by CodeSource path (?P<location>.+) and passing to app \"(?P<application>.*)\"$"),
    #     # - Adding {} to library usage for lib {} in application '{}''
    #     'used': re.compile(
    #         r"\- Adding (?P<fqcn>\S+) to library usage for lib (?P<jarname>\S+) in app (?P<location>~NOLOC~)?\".+\" \((?P<application>.*)\)$"),
    #     # default type will be a misfit
    #     Shred.DEFAULT_TYPE: re.compile(r"^~NOMATCH~$")
    # }
    # value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)
    value_extractor = ShredValueExtractor()     # extracts nothing

    insert_columns = ['line', 'type', 'req', 'resp', 'url', 'crumbthread', 'crumbtime', 'stackframe']


    def __init__(self):
        super().__init__(
                         tbl_creator=ChtiShred.tbl_creator,
                         entry_selector=ChtiShred.entry_selector,
                         entry_classifier=ChtiShred.entry_classifier,
                         value_extractor=ChtiShred.value_extractor,
                         insert_columns=ChtiShred.insert_columns
                         )

    def transform_values(self, line, entry, type, extracted_vals):
        return line, type, -1, -1, '', '', '', entry

if __name__ == '__main__':
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")

    debug_db = path.join('', logname + '.db')
    connection = createdb.connectdb(debug_db)
    chtiShred = ChtiShred()
    chtiShred.initialize_tables(connection)
