import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor

class MesgShred(Shred):
    tbl_name = 'mesg'
    misfits_tbl_name = 'cont'
    create_tbl_sql = """
create table mesg(
line integer primary key references log(line),
timestamp datetime not null,
thread text not null,
logger text not null,
level text not null,
message text not null)
"""
    tbl_index_sqls = [
        'create index idx_mesg_logger on mesg(logger)',
        'create index idx_mesg_level_package on mesg(level)'
    ]
    create_misfits_sql = """
create table cont(
line integer primary key references log(line),
mesg integer key references mesg(line))    
"""
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls,
        misfits_tbl_name, create_misfits_sql)

    entry_selector = ShredEntrySelector(batch_size=2000)   # selects all by default
    entry_classifier = ShredEntryClassifier()   # just one default type

    # "YYYY-MM-DD HH:MM:SS.SSS"
    # 2020-05-25 18:33:53,897 [http-nio-8080-exec-10 CapturingHttpItem] DEBUG -
    #      CRUMB request@772027798 /petclinic/oups.html		CONTEXT_SWITCH 2020-05-25 18:33:53,897 Catalina-utility-2 ==> http-nio-8080-exec-10

    extracted_val_names=['timestamp', 'thread', 'logger', 'level', 'message']
    value_extractors = {
        Shred.DEFAULT_TYPE: re.compile(
            r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(?P<thread>.+) (?P<logger>\S+)\] (?P<level>\S+) -( (?P<message>.*))?$")
    }
    value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)

    insert_columns = ["line", "timestamp", "thread", "logger", "level", "message"]
    insert_misfits_sql = 'insert into {} (line, mesg) values (?,?)'.format(misfits_tbl_name)

    def __init__(self):
        super().__init__(
            tbl_creator=MesgShred.tbl_creator,
            entry_selector=MesgShred.entry_selector,
            entry_classifier=MesgShred.entry_classifier,
            value_extractor=MesgShred.value_extractor,
            insert_columns=MesgShred.insert_columns,
            insert_misfits_sql=MesgShred.insert_misfits_sql,
            show_misfits=False
            )

    def transform_values(self, line, entry, type, extracted_vals):
        return line, extracted_vals["timestamp"], extracted_vals["thread"], extracted_vals["logger"], extracted_vals["level"], extracted_vals["message"]

    def transform_misfits(self, line, last_good_line):
        return (line, last_good_line)

select_multiline_entries_sql = """
select line, entry
from log
where line in (
    select distinct mesg
    from cont
    UNION
    select line from cont
)
order by line
"""

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")

    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    mesgShred = MesgShred()
    mesgShred.initialize_tables(connection)
