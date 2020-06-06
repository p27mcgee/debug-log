import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor

class LmclShred(Shred):
    tbl_name = "lmcl"
    create_tbl_sql = \
"""create table lmcl(
        line integer primary key references log(line),
        class text not null,
        package text not null,
        result text,
        location text,
        adapters text)"""
    tbl_index_sqls = [
        "create index idx_lmcl_package on lmcl(package)",
        "create index idx_lmcl_class_package on lmcl(class, package)"
    ]
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls)

    entry_signature = "!LM!ClassLoad|"
    entry_selector = ShredEntrySelector(entry_signature)

    entry_classifier = ShredEntryClassifier()

    extracted_val_names=['fqcn', 'result', 'adapters', 'location']
    value_extractors = {
    Shred.DEFAULT_TYPE: re.compile(
        r"\!LM\!ClassLoad\|(?P<fqcn>[^|]+)\|result\=(?P<result>[^&]+)\&adapters\=(?P<adapters>[^&]*)\&location\=(?P<location>.*)$")
    }
    value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)

    insert_columns = ["line", "class", "package", "result", "location", "adapters"]

    def __init__(self):
        super().__init__(
                         tbl_creator=LmclShred.tbl_creator,
                         entry_selector=LmclShred.entry_selector,
                         entry_classifier=LmclShred.entry_classifier,
                         value_extractor=LmclShred.value_extractor,
                         insert_columns=LmclShred.insert_columns
                         )

    def transform_values(self, line, entry, type, extracted_vals):
        classname, package = self.classAndPackage(extracted_vals["fqcn"])
        return line, classname, package, extracted_vals["result"], extracted_vals["location"], extracted_vals["location"]


logname = "sb-san-petclinic"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    lcmlShred = LmclShred()
    lcmlShred.initialize_tables(connection)
