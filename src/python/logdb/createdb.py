import sqlite3
from os import path

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

def initialize_log_table(infile, cursor):
    print("Initializing log table from {}".format(infile))
    total = 0
    # truncate log table
    cursor.execute("delete from log")
    with open(infile, 'r') as inlog:
        chunk = []
        for idx, entry in enumerate(inlog):
            chunk.append((idx + 1, entry.strip()))
            if idx % chunksize == chunksize - 1:
                total += add_chunk_of_log_enties(chunk, cursor)
                print(".", end ="")
                chunk.clear()
        total += add_chunk_of_log_enties(chunk, cursor)
    print("\nAdded {} rows".format(str(total)))

def create_log_table(cursor):
    sql = "create table if not exists log(line integer primary key, entry text)"
    cursor.execute(sql)

def connectdb(dbname):
    return sqlite3.connect(dbname, isolation_level=None)

def create_log_db(log_path, dbname):
    connection = connectdb(dbname)
    cursor = connection.cursor()
    create_log_table(cursor)
    initialize_log_table(log_path, cursor)
    cursor.close()
    return connection

logname = "petclinic"
log_dir = "data"

if __name__ == "__main__":
    petclinic_log = path.join(log_dir, logname + ".log")
    petclinit_db = path.join("", logname + ".db")
    create_log_db(petclinic_log, petclinit_db)