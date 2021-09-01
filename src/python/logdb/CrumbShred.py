import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor

WIP

class CrumbShred(Shred):
    tbl_name = "crumb"
    create_tbl_sql = \
"""create table crumb(
line integer primary key references log(line),
type text not null, 
class text,
package text,
application text,
location text)"""
    tbl_index_sqls = [
                           "create index idx_crumb_package on crumb(package)",
                           "create index idx_crumb_class_package on crumb(class, package)"
                       ]
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls)

    entry_signature = " - CRUMB "
    entry_selector = ShredEntrySelector(entry_signature)

    # each entry is either req or resp and one of begin, end, callstack or context
    # "req": " request@",
    # "resp": " response@",
    type_signatures = {
        "hist_beg": "\t\t\tBEGIN ",
        "begin": "\t\tBEGIN ",
        "end": "END & HISTORY:",
        "hist_end": "\t\t\tEND ",
        "hist_ctx": "\t\t\tCONTEXT_SWITCH",
        "context": "\t\tCONTEXT_SWITCH",
        "callstack": "\t\t\t\t"
    }
    entry_classifier = ShredEntryClassifier(type_signatures)

    extracted_val_names=["thrd", "req", "resp", "url", ]
    value_extractors = {
        # - Not putting java.util.Hashtable$KeySet in orphanage as its from bootstrapped classloade
        "hist_beg": re.compile(
            r"\- Not putting (?P<fqcn>\S+) in orphanage as its from (?P<location>~NOLOC~)?(?P<application>~NOAPP~)?"),
        # - Couldn't find app for org.jboss.Main$ShutdownHook with CodeSource location file:/opt/jboss/bin/run.jar
        "begin": re.compile(
            r"\- Couldn't find app for (?P<fqcn>\S+) with CodeSource path (?P<application>~NOAPP~)?(?P<location>.*)$"),
        # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
        "end": re.compile(r"\- Adding (?P<fqcn>\S+) to orphanage(?P<location>~NOLOC~)?(?P<application>~NOAPP~)?$"),
        # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
        "hist_end": re.compile(
            r"\- Adding (?P<fqcn>\S+) to list of missed classload events for uninventoried (?P<location>~NOLOC~)?(?P<application>.*)$"),
        # - url @detectLibraryClass vfs:/opt/jboss/server/default/deploy/jbossweb.sar/jbossweb.jar/ contains org.apache.tomcat.util.buf.C2BConverter for application "platform-servlet"
        "hist_ctx": re.compile(
            r"\- url \@detectLibraryClass (?P<location>.+) contains (?P<fqcn>\S+) for app \".+\" \((?P<application>.*)\)$"),
        "context": re.compile(
            r"\- No library found for \S+ in app \".+\" (?P<location>~NOLOC~)?(?P<fqcn>~NOCLASS~)?\((?P<application>.*)\)$"),
        # - Took {} from orphanage by CodeSource path {} and passing to app {}
        "callstack": re.compile(
            r"\- Took (?P<fqcn>\S+) from orphanage by CodeSource path (?P<location>.+) and passing to app \"(?P<application>.*)\"$"),
        # default type will be a misfit
        Shred.DEFAULT_TYPE: re.compile(r"^~NOMATCH~$")
    }
    value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)

    insert_columns = ["line", "type", "class", "package", "application", "location"]


    def __init__(self):
        super().__init__(
                         tbl_creator=CrumbShred.tbl_creator,
                         entry_selector=CrumbShred.entry_selector,
                         entry_classifier=CrumbShred.entry_classifier,
                         value_extractor=CrumbShred.value_extractor,
                         insert_columns=CrumbShred.insert_columns
                         )

    def transform_values(self, line, entry, type, extracted_vals):
        classname, package = self.classAndPackage(extracted_vals["fqcn"])
        return line, type, classname, package, extracted_vals["application"], extracted_vals["location"]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")

    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    crumbShred = CrumbShred()
    crumbShred.initialize_tables(connection)
