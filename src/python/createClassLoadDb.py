from os import path
from src.python.logdb.createdb import create_log_db
from src.python.logdb.add_tech_tbl import initialize_tech_table
from src.python.logdb.add_pmcl_tbl import initialize_pmcl_table
import src.python.logdb.logdb_sql as logdb_sql

def make_file_path(dir, log_ext, log_name):
    filename = log_name + log_ext
    return path.join(dir, filename)

def drop_table(cursor, table):
    cursor.execute("drop table if exists {}".format(table))

def display_table_rowcount(cursor, table):
    cursor.execute("select count(*) from {}".format(table))
    count, = cursor.fetchone()
    print("Table {} contains {} log lines".format(table, str(count)));

log_name = "petclinic"
log_ext = ".log"
log_dir = "data"
db_name = log_name
db_ext = ".db"
db_dir = ""

if __name__ == "__main__":
    log_path = make_file_path(log_dir, log_ext, log_name)
    db_path = make_file_path(db_dir, db_ext, db_name)
    connection = create_log_db(log_path, db_path)
    initialize_tech_table(connection)
    initialize_pmcl_table(connection)
    cursor = connection.cursor()

    print("\nCreating classinfo table...")
    drop_table(cursor, "classinfo")
    cursor.execute(logdb_sql.create_classinfo_tbl_sql)
    display_table_rowcount(cursor, "classinfo")


