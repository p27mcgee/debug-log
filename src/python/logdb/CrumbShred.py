import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor

# WIP

class CrumbShred(Shred):
    tbl_name = "crumb"
    create_tbl_sql = \
"""create table crumb(
line integer primary key references log(line),
type text, 
req text,
resp text,
url text,
crumbthread text,
crumbtime datetime,
stackframe text)"""
    tbl_index_sqls = [
                           "create index idx_crumb_url on crumb(url)",
                ]
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls)

    entry_signature = " CRUMB "        # what about !LM!RequestTime|RequestEnded
    entry_selector = ShredEntrySelector(entry_signature)

    # each entry is either req or resp and one of begin, end, callstack or context
    # "req": " request@",
    # "resp": " response@",
    type_signatures = {
        "hist_beg": "\t\t\tBEGIN ",
        "begin": "\t\tBEGIN ",
        "end": "END & HISTORY:",
        # what about !LM!RequestTime|RequestEnded
    }
    entry_classifier = ShredEntryClassifier(type_signatures)

    extracted_val_names=["req", "resp", "url", "crumbthread", "crumbtime", "stackframe"]
    value_extractors = {
        # - Not putting java.util.Hashtable$KeySet in orphanage as its from bootstrapped classloade
        "hist_beg": re.compile(r"XXX"),
        # - Couldn't find app for org.jboss.Main$ShutdownHook with CodeSource location file:/opt/jboss/bin/run.jar
        "begin": re.compile(r"- CRUMB request@(?P<req>\S+) (?P<url>\S+)\t\tBEGIN \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} (?P<crumbthread>\S+)(?P<resp>~NORESP~)?(?P<stackframe>~NOFRAME~)?(?P<crumbtime>~NOFRAME~)?$"),
        "end": re.compile(r"XXX"),
        # default type will be a misfit
        Shred.DEFAULT_TYPE: re.compile(r"^~NOMATCH~$")
    }
    value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)

    insert_columns = ["line", "type", "req", "resp", "url", "crumbthread", "crumbtime", "stackframe"]

    def __init__(self):
        super().__init__(
                         tbl_creator=CrumbShred.tbl_creator,
                         entry_selector=CrumbShred.entry_selector,
                         entry_classifier=CrumbShred.entry_classifier,
                         value_extractor=CrumbShred.value_extractor,
                         insert_columns=CrumbShred.insert_columns
                         )

    def transform_values(self, line, entry, type, extracted_vals):
        return line, type, extracted_vals["req"], extracted_vals["resp"], extracted_vals["url"], extracted_vals["crumbthread"], extracted_vals["crumbtime"], entry # extracted_vals["stackframe"]


if __name__ == "__main__":
    testline = "- CRUMB request@664592038 /ping		BEGIN 2024-10-21 19:42:28,477 reactor-http-nio-2"
    regex = re.compile(r"- CRUMB request@(?P<req>\d+) (?P<url>\S+)\t\tBEGIN \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} (?P<thrd>\S+)(?P<resp>~NORESP~)?$")
    match = regex.search(testline)
    for extracted_val_name in ["req", "url", "thrd"]:
        print("{}: {}".format(extracted_val_name, str(match.group(extracted_val_name))))


