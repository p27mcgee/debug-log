import sqlite3
import contextlib
from os import path
import sys

SHOW_PROGRESS = False

def classAndPackage(fqcn):
    lastdot = fqcn.rfind('.')
    classname = fqcn[lastdot + 1:]
    package = fqcn[:lastdot]
    return classname, package

def quotOrNull(txt):
    if txt == None:
        return "NULL"
    else:
        return "'" + txt + "'"

chunksize = 10000;

def add_chunk_of_log_enties(chunk, cursor):
    cursor.execute("begin transaction")
    result = cursor.executemany("insert into log values(?,?)", chunk)
    cursor.execute("commit")
    return len(chunk)

def initialize_log_table(infile, connection):
    print("Initializing log table from {} ...".format(infile))
    total = 0
    with contextlib.closing(connection.cursor()) as cursor:
        # truncate log table
        cursor.execute("delete from log")
        with open(infile, 'r') as inlog:
            chunk = []
            for idx, entry in enumerate(inlog):
                chunk.append((idx + 1, entry.rstrip("\n")))
                if idx % chunksize == chunksize - 1:
                    total += add_chunk_of_log_enties(chunk, cursor)
                    if SHOW_PROGRESS:
                        print(".", end ="")
                    chunk.clear()
            total += add_chunk_of_log_enties(chunk, cursor)
    if SHOW_PROGRESS:
        print("\n")
    print("Added {} rows to table {}".format(str(total), "log"))

def create_log_table(connection):
    with contextlib.closing(connection.cursor()) as cursor:
        cursor.execute("create table if not exists log(line integer primary key, entry text)")

def connectdb(dbname):
    return sqlite3.connect(dbname, isolation_level=None)

def create_log_db(log_path, dbname):
    connection = connectdb(dbname)
    create_log_table(connection)
    initialize_log_table(log_path, connection)
    return connection

log_dir = "data"

def main(logname):
    debug_log = path.join(log_dir, logname + ".err")
    debug_db = path.join("", logname + ".db")
    return create_log_db(debug_log, debug_db)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")
    main(logname)