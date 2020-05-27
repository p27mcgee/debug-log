import sqlite3
import re
import src.python.logdb.createdb as createdb
from src.python.logdb.createdb import classAndPackage
from src.python.logdb.createdb import quotOrNull

# "YYYY-MM-DD HH:MM:SS.SSS"
# 2020-05-25 18:33:53,897 [http-nio-8080-exec-10 CapturingHttpItem] DEBUG -
# CRUMB request@772027798 /petclinic/oups.html		CONTEXT_SWITCH 2020-05-25 18:33:53,897 Catalina-utility-2 ==> http-nio-8080-exec-10
value_extractor = re.compile(r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(?P<thread>.+) (?P<logger>\S+)\] (?P<level>\S+) -( (?P<message>.*))?$")

def initialize_mesg_tables(connection):
    cursor = connection.cursor()
    drop_sql = "drop table if exists mesg"
    cursor.execute(drop_sql)
    create_sql = """create table mesg(
        line integer primary key references log(line),
        timestamp datetime not null,
        thread text not null,
        logger text not null,
        level text not null,
        message text not null)
    """
    cursor.execute(create_sql)

    # add indexes
    mesg_logger_idx_sql = "create index idx_mesg_logger on mesg(logger)"
    cursor.execute(mesg_logger_idx_sql)
    mesg_level_idx_sql = "create index idx_mesg_level_package on mesg(level)"
    cursor.execute(mesg_level_idx_sql)

    create_cont_table(connection)

    # populate
    nrows = 0
    last_mesg = -1
    nmesg = 0
    ncont = 0
    select_mesg_sql = "select line, entry from log"
    cursor.execute(select_mesg_sql)
    while True:
        print(".", end="")
        rows = cursor.fetchmany(1000)
        if len(rows) == 0:
            cursor.close()
            break
        last_mesg, added_mesg, added_cont = add_mesg_rows(rows, last_mesg, connection)
        nrows += len(rows)
        nmesg += added_mesg
        ncont += added_cont
    print("\nAdded {} rows to table mesg".format(str(nmesg)))
    print("\nAdded {} rows to table cont".format(str(ncont)))

def add_mesg_rows(log_mesg_rows, last_mesg, connection):
    insert_mesg_sql = "insert into mesg (line, timestamp, thread, logger, level, message) values (?,?,?,?,?,?)"
    insert_cont_sql = "insert into cont (line, mesg) values (?,?)"
    cursor = connection.cursor()
    cursor.execute('begin transaction')
    nmesg = 0
    ncont = 0
    for line, entry in log_mesg_rows:
        try:
            timestamp, thread, logger, level, message = value_extractor.match(entry).group('timestamp', 'thread', 'logger', 'level', 'message')
            timestamp = timestamp.replace(',', '.')
            if message == None:
                message = ""
            last_mesg = line
            cursor.execute(insert_mesg_sql, (line, timestamp, thread, logger, level, message))
            nmesg += 1
        except:
            cursor.execute(insert_cont_sql, (line, last_mesg))
            ncont += 1
    cursor.execute('commit')
    cursor.close
    return last_mesg, nmesg, ncont

def create_cont_table(connection):
    cursor = connection.cursor()
    drop_sql = "drop table if exists cont"
    cursor.execute(drop_sql)
    create_sql = """create table cont(
        line integer primary key references log(line),
        mesg integer key references mesg(line)
        )
    """
    cursor.execute(create_sql)

dbname = "petclinic"

if __name__ == "__main__":
    connection = createdb.connectdb(dbname + ".db")
    initialize_mesg_tables(connection)