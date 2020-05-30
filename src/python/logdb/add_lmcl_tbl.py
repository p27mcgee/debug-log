import sqlite3
import re
import src.python.logdb.createdb as createdb
from src.python.logdb.createdb import classAndPackage
from urllib.parse import unquote as urldecode

entry_signature = "!LM!ClassLoad|"
value_extractor = re.compile(r"\!LM\!ClassLoad\|(?P<fqcn>[^|]+)\|result\=(?P<result>[^&]+)\&adapters\=(?P<adapters>[^&]*)\&location\=(?P<location>.*)$")
table_name = "lmcl"
misfits_table_name = "lmcl_misfits"
select_entries_sql = "select line, entry from log where entry like '%" + entry_signature + "%'"

drop_table_sql = "drop table if exists lmcl"
create_sql = """create table lmcl(
        line integer primary key references log(line),
        class text not null,
        package text not null,
        result text,
        location text,
        adapters text)
    """
table_index_sqls = [
    "create index idx_lmcl_package on lmcl(package)",
    "create index idx_lmcl_class_package on lmcl(class, package)"
]
drop_misfits_sql = "drop table if exists lmcl_misfits"
create_misfits_sql = "create table lmcl_misfits(line integer primary key references log(line))"
insert_sql = "insert into lmcl (line, class, package, result, location, adapters) values (?, ?, ?, ?, ?, ?)"
insert_misfits_sql = "insert into lmcl_misfits (line) values (?)"

def transform_values(line, entry, extracted_vals):
    fqcn, result, adapters, location = extracted_vals
    classname, package = classAndPackage(fqcn)
    decoded_location = urldecode(location)
    if "%" in decoded_location:
        print (decoded_location + " vs. " + location)
    return line, classname, package, result, decoded_location, adapters

def initialize_tables(connection):
    cursor = connection.cursor()
    create_table(cursor)
    create_misfits_table(cursor)
    cursor.close()
    populate_tables(connection)

def create_table(cursor):
    cursor.execute(drop_table_sql)
    cursor.execute(create_sql)
    for index_sql in table_index_sqls:
        cursor.execute(index_sql)

def create_misfits_table(cursor):
    cursor.execute(drop_misfits_sql)
    cursor.execute(create_misfits_sql)

def populate_tables(connection):
    cursor = connection.cursor()
    totalAdded = 0
    totalMisfits = 0
    cursor.execute(select_entries_sql)
    while True:
        print(".", end="")
        rows = cursor.fetchmany(1000)
        if len(rows) == 0:
            cursor.close()
            break
        nAdded, nMisfits = add_rows(rows, connection)
        totalAdded += nAdded
        totalMisfits += nMisfits
    print("\nAdded {} rows to table {}".format(str(totalAdded), table_name))
    print("Added {} rows to table {}".format(str(totalMisfits), misfits_table_name))
    cursor.close()

def add_rows(log_rows, connection):
    cursor = connection.cursor()
    cursor.execute("begin transaction")
    values = []
    misfits = []
    nAdded = 0
    nMisfits = 0
    for line, entry in log_rows:
        try:
            extracted_vals = value_extractor.search(entry).group('fqcn', 'result', 'adapters', 'location')
            values.append(transform_values(line, entry, extracted_vals))
            nAdded += 1
        except:
            print("No match for extractor regex in entry line {}: {}".format(str(line), entry))
            misfits.append(line,)
            nMisfits += 1
    cursor.executemany(insert_sql, values);
    cursor.executemany(insert_misfits_sql, misfits);
    cursor.execute("commit")
    cursor.close()
    return nAdded, nMisfits

def initialize_lmcl_table(connection):
    initialize_tables(connection)

if __name__ == "__main__":
    connection = createdb.connectdb("JBoss-platform.db")
    initialize_lmcl_table(connection)