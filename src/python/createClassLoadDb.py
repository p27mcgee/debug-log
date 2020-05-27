from os import path
from src.python.logdb.createdb import create_log_db
from src.python.logdb.add_tech_tbl import initialize_tech_table
from src.python.logdb.add_pmcl_tbl import initialize_pmcl_table
import src.python.logdb.logdb_sql as logdb_sql
import  src.python.summarizeWebAppClassUsage as summarizeWebAppClassUsage

def make_file_path(dir, log_ext, log_name):
    filename = log_name + log_ext
    return path.join(dir, filename)

def drop_table(cursor, table):
    cursor.execute("drop table if exists {}".format(table))

def display_table_rowcount(cursor, table):
    cursor.execute("select count(*) from {}".format(table))
    count, = cursor.fetchone()
    print("Table {} contains {} log lines".format(table, str(count)));

def display_removed_rowcount(cursor, table):
    print("Removed {} rows from table {}.".format(str(cursor.rowcount), table));

def filter_classinfo_using_heuristics(cursor):
    print("\nRemove from classinfo table the TechnologyClassListener log entries reporting \"not putting ? in orphanage as its from bootstrapped classloader\"")
    print("These are not web app classes and they also have null ClassLoader and CoseSource location info.")
    print("Removing tech.type = 'noput' entries from classinfo table...")
    cursor.execute(logdb_sql.remove_tech_noput_classes_from_classinfo_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    print("\nRemove from classinfo table the TechnologyClassListener log entries reporting \"Couldn't find app for \" which do not report use of ParallelWebappClassLoader.")
    print("This removes some servlet container implementation classes.")
    print("THIS IS LIKELY A TOMCAT SPECIFIC APPROACH REQUIRING GENERALIZATION.")
    print("Removing tech.type = 'noapp' and classloader <> \"ParallelWebappClassLoader\" entries from classinfo table...")
    cursor.execute(logdb_sql.remove_tech_noapp_not_PWCL_classes_from_classinfo_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    print("\nRemove from classinfo table the !PM!ClassLoad log entries with NULL_ProtectionDomain.")
    print("This removes dynamic proxy, lambda and some JDK reflection classes.")
    print("Removing pmcl.location == \"NULL_ProtectionDomain\" entries from classinfo table...")
    cursor.execute(logdb_sql.remove_pmcl_NULL_ProtectionDomain_classes_from_classinfo_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    print("\nRemove from classinfo table the !PM!ClassLoad log entries with result UNTOUCHABLE.")
    print("This removes Contrast agent classes and some lambda and JDK reflection classes.")
    print("Removing pmcl.result == \"UNTOUCHABLE\" entries from classinfo table...")
    cursor.execute(logdb_sql.remove_pmcl_result_UNTOUCHABLE_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")


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

    # this is useful only as an independent validation of the location
    # WEB-INF class filter
    # filter_classinfo_using_heuristics(cursor)

    summarizeWebAppClassUsage.main(db_path)


