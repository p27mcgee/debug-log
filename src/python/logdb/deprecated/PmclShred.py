import re
import sys
from os import path
from urllib.parse import unquote_plus as urldecode
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor


class PmclShred(Shred):
    tbl_name = "pmcl"
    create_tbl_sql = \
"""create table pmcl(
        line integer primary key references log(line),
        type text,
        class text not null,
        package text not null,
        classloader text,
        location text,
        result text)"""
    tbl_index_sqls = [
        "create index idx_pmcl_type on pmcl(type)",
        "create index idx_pmcl_package on pmcl(package)",
        "create index idx_pmcl_class_package on pmcl(class, package)",
        "create index idx_pmcl_classloader on pmcl(classloader)"
    ]
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls)

    entry_signature = "!PM!ClassLoad|"
    entry_selector = ShredEntrySelector(entry_signature)

    entry_classifier = ShredEntryClassifier()

    extracted_val_names=['fqcn', 'classloader', 'location', 'result']
    value_extractors = {
    Shred.DEFAULT_TYPE: re.compile(
        r"\!PM\!ClassLoad\|(?P<fqcn>[^|]+)\|classloader\=(?P<classloader>[^&]+)\&location\=(?P<location>[^&]+)\&result\=(?P<result>.+)$")
    }
    value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)

    insert_columns = ["line", "class", "package", 'classloader', 'location', 'result']

    def __init__(self):
        super().__init__(
                         tbl_creator=PmclShred.tbl_creator,
                         entry_selector=PmclShred.entry_selector,
                         entry_classifier=PmclShred.entry_classifier,
                         value_extractor=PmclShred.value_extractor,
                         insert_columns=PmclShred.insert_columns
                         )

    def transform_values(self, line, entry, type, extracted_vals):
        classname, package = self.classAndPackage(extracted_vals["fqcn"])
        return line, classname, package, \
               urldecode(extracted_vals["classloader"]), \
               urldecode(extracted_vals["location"]), \
               extracted_vals["result"]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")

    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    lcmlShred = PmclShred()
    lcmlShred.initialize_tables(connection)
