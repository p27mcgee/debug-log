from os import path
from urllib.parse import unquote as urldecode
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

def display_removed_rowcount(cursor, table):
    print("Removed {} rows from table {}.".format(str(cursor.rowcount), table));

def summarize_web_app_class_usage(cursor):
    print("\nAfter appropriately excluding system and server classes the following Web App classes remain:")
    locprefix = ""
    prefixlen = 0
    for classcount, location, package in cursor.execute(logdb_sql.select_web_app_location_package_counts):
        if prefixlen == 0 and "apache-tomcat" in location:
            decoded_location = urldecode(location)
            tomcat_at = decoded_location.find("/apache-tomcat")
            if tomcat_at != -1:
                locprefix = decoded_location[:tomcat_at+1]
                prefixlen = len(locprefix)
        dec_loc = urldecode(location)
        if (prefixlen != 0 and dec_loc.startswith(locprefix)):
            dec_loc = dec_loc[prefixlen:]
        print("{} classes in package {} from {}".format(str(classcount), package, dec_loc))

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

    print("\nRemove from classinfo table the TechnologyClassListener log entries reporting \"not putting ? in orphanage as its from bootstrapped classloader\"")
    print("These are not web app classes and they also null ClassLoader and CoseSource location info.")
    print("\nRemoving tech.type = 'noput' entries from classinfo table...")
    result = cursor.execute(logdb_sql.remove_tech_noput_classes_from_classinfo_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    print("\nRemove from classinfo table the TechnologyClassListener log entries reporting \"Couldn't find app for \" which do not report use of ParallelWebappClassLoader.")
    print("This removes some servlet container implementation classes.")
    print("THIS IS LIKELY A TOMCAT SPECIFIC APPROACH REQUIRING GENERALIZATION.")
    print("\nRemoving tech.type = 'noapp' and classloader <> \"ParallelWebappClassLoader\" entries from classinfo table...")
    result = cursor.execute(logdb_sql.remove_tech_noapp_not_PWCL_classes_from_classinfo_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    print("\nRemove from classinfo table the !PM!ClassLoad log entries with NULL_ProtectionDomain.")
    print("This removes dynamic proxy, lambda and some JDK reflection classes.")
    print("\nRemoving pmcl.location == \"NULL_ProtectionDomain\" entries from classinfo table...")
    result = cursor.execute(logdb_sql.remove_pmcl_NULL_ProtectionDomain_classes_from_classinfo_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    print("\nRemove from classinfo table the !PM!ClassLoad log entries with result UNTOUCHABLE.")
    print("This removes Contrast agent classes and some lambda and JDK reflection classes.")
    print("\nRemoving pmcl.result == \"UNTOUCHABLE\" entries from classinfo table...")
    result = cursor.execute(logdb_sql.remove_pmcl_result_UNTOUCHABLE_sql)
    display_removed_rowcount(cursor, "classinfo")
    display_table_rowcount(cursor, "classinfo")

    summarize_web_app_class_usage(cursor)


